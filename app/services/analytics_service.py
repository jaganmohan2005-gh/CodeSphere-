"""
CodeSphere - Analytics & Metrics Service
----------------------------------------
Calculates real-time, database-backed performance analytics for students
and platform-wide aggregates for administrators. Handled with defensive
checks to prevent division-by-zero errors and empty record exceptions.
"""

from sqlalchemy import func
from app.extensions import db
from app.models.user import User
from app.models.question import Question, Category
from app.models.assessment import Assessment, AssessmentAttempt
from app.models.submission import Submission, StudentProgress


class AnalyticsService:
    """
    Computes statistical indicators, proficiency rankings, and aggregations
    directly from active database models.
    """

    @staticmethod
    def get_student_analytics(user_id: int) -> dict:
        """
        Calculates comprehensive metrics for an individual student.
        """
        user = db.session.get(User, user_id)
        if not user:
            return {}

        # 1. Total Distinct Questions Attempted and Solved
        # Query distinct question IDs from submissions
        attempted_q_ids = db.session.query(Submission.question_id)\
            .filter(Submission.user_id == user_id)\
            .distinct().all()
        total_attempted = len(attempted_q_ids)

        solved_q_ids = db.session.query(Submission.question_id)\
            .filter(Submission.user_id == user_id, Submission.status == 'Accepted')\
            .distinct().all()
        total_solved = len(solved_q_ids)

        # Defensive accuracy calculation
        accuracy = round((total_solved / total_attempted * 100.0), 1) if total_attempted > 0 else 0.0

        # 2. Assessment Attempts Breakdown
        attempts = AssessmentAttempt.query.filter_by(user_id=user_id)\
            .order_by(AssessmentAttempt.created_at.desc()).all()
        
        completed_attempts = [a for a in attempts if a.status in ['completed', 'timed_out', 'evaluated']]
        assessments_taken = len(completed_attempts)
        assessments_passed = sum(1 for a in completed_attempts if a.is_passed)
        
        total_score_sum = sum(a.percentage for a in completed_attempts)
        avg_assessment_score = round(total_score_sum / assessments_taken, 1) if assessments_taken > 0 else 0.0
        highest_assessment_score = round(max((a.percentage for a in completed_attempts), default=0.0), 1)

        # 3. Topic-Wise Performance from Categories
        categories = Category.query.all()
        topic_performance = []
        weak_topics = []
        strong_topics = []

        for cat in categories:
            # Query questions in this category attempted by student
            cat_q_ids = [q.id for q in cat.questions]
            if not cat_q_ids:
                continue

            cat_attempted = db.session.query(Submission.question_id)\
                .filter(Submission.user_id == user_id, Submission.question_id.in_(cat_q_ids))\
                .distinct().count()

            cat_solved = db.session.query(Submission.question_id)\
                .filter(Submission.user_id == user_id, Submission.question_id.in_(cat_q_ids), Submission.status == 'Accepted')\
                .distinct().count()

            cat_accuracy = round((cat_solved / cat_attempted * 100.0), 1) if cat_attempted > 0 else 0.0

            item = {
                'category_id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'icon': cat.icon,
                'attempted': cat_attempted,
                'solved': cat_solved,
                'accuracy': cat_accuracy,
                'total_in_cat': len(cat_q_ids)
            }
            topic_performance.append(item)

            if cat_attempted > 0:
                if cat_accuracy < 50.0:
                    weak_topics.append(cat.name)
                elif cat_accuracy >= 70.0:
                    strong_topics.append(cat.name)

        # 4. Recent Submissions
        recent_submissions = Submission.query.filter_by(user_id=user_id)\
            .order_by(Submission.submitted_at.desc())\
            .limit(10).all()

        return {
            'user': user,
            'total_attempted': total_attempted,
            'total_solved': total_solved,
            'accuracy_percentage': accuracy,
            'assessments_taken': assessments_taken,
            'assessments_passed': assessments_passed,
            'avg_assessment_score': avg_assessment_score,
            'highest_assessment_score': highest_assessment_score,
            'topic_performance': topic_performance,
            'weak_topics': weak_topics,
            'strong_topics': strong_topics,
            'recent_submissions': recent_submissions,
            'assessment_history': completed_attempts
        }

    @staticmethod
    def get_admin_dashboard_stats() -> dict:
        """
        Aggregates platform-wide figures for the administrative control panel.
        All values are derived directly from actual database rows.
        """
        total_students = User.query.filter_by(role='student').count()
        total_questions = Question.query.count()
        total_assessments = Assessment.query.count()

        completed_attempts = AssessmentAttempt.query\
            .filter(AssessmentAttempt.status.in_(['completed', 'timed_out', 'evaluated'])).all()
        completed_count = len(completed_attempts)

        total_percentages = sum(a.percentage for a in completed_attempts)
        avg_student_score = round(total_percentages / completed_count, 1) if completed_count > 0 else 0.0

        # Question difficulty distribution
        easy_count = Question.query.filter_by(difficulty='Easy').count()
        medium_count = Question.query.filter_by(difficulty='Medium').count()
        hard_count = Question.query.filter_by(difficulty='Hard').count()

        # Category distribution
        categories = Category.query.all()
        category_stats = [{
            'id': c.id,
            'name': c.name,
            'count': c.questions.count()
        } for c in categories]

        # Recent Platform Activities (latest 10 submissions across all students)
        recent_submissions = Submission.query.order_by(Submission.submitted_at.desc()).limit(8).all()
        recent_attempts = AssessmentAttempt.query.order_by(AssessmentAttempt.created_at.desc()).limit(8).all()

        return {
            'total_students': total_students,
            'total_questions': total_questions,
            'total_assessments': total_assessments,
            'completed_assessments': completed_count,
            'avg_student_score': avg_student_score,
            'difficulty_breakdown': {
                'Easy': easy_count,
                'Medium': medium_count,
                'Hard': hard_count
            },
            'category_stats': category_stats,
            'recent_submissions': recent_submissions,
            'recent_attempts': recent_attempts
        }


# Singleton analytics service instance
analytics_service = AnalyticsService()
