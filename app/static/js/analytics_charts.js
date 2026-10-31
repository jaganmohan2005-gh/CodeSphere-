/**
 * CodeSphere - Performance & Analytics Charts Controller
 * -----------------------------------------------------
 * Renders interactive Chart.js visualizations for students and administrators.
 */

window.renderStudentAnalyticsCharts = function (data) {
  // 1. Accuracy Doughnut Chart
  const doughnutCtx = document.getElementById('accuracyDoughnutChart');
  if (doughnutCtx) {
    const solved = data.total_solved || 0;
    const attempted = data.total_attempted || 0;
    const unsolved = Math.max(0, attempted - solved);

    new Chart(doughnutCtx, {
      type: 'doughnut',
      data: {
        labels: ['Solved (Accepted)', 'Attempted (Unsolved)'],
        datasets: [{
          data: [solved, unsolved],
          backgroundColor: ['#10b981', '#cbd5e1'],
          borderWidth: 2,
          borderColor: '#ffffff',
          hoverOffset: 4
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' }
        },
        cutout: '72%'
      }
    });
  }

  // 2. Topic-wise Performance Chart
  const topicCtx = document.getElementById('topicPerformanceBarChart');
  if (topicCtx && data.topic_performance) {
    const labels = data.topic_performance.map(t => t.name);
    const accuracies = data.topic_performance.map(t => t.accuracy);
    const solvedCounts = data.topic_performance.map(t => t.solved);

    new Chart(topicCtx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Accuracy Rate (%)',
          data: accuracies,
          backgroundColor: '#2563eb',
          borderRadius: 6
        }, {
          label: 'Questions Solved',
          data: solvedCounts,
          backgroundColor: '#06b6d4',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            grid: { color: '#f1f5f9' }
          },
          x: {
            grid: { display: false }
          }
        },
        plugins: {
          legend: { position: 'top' }
        }
      }
    });
  }

  // 3. Assessment History Progression Line Chart
  const lineCtx = document.getElementById('assessmentHistoryLineChart');
  if (lineCtx && data.assessment_history) {
    const labels = data.assessment_history.map(a => a.assessment ? a.assessment.title : `Assessment #${a.id}`);
    const scores = data.assessment_history.map(a => a.percentage);

    new Chart(lineCtx, {
      type: 'line',
      data: {
        labels: labels.length ? labels : ['No Assessments Completed'],
        datasets: [{
          label: 'Score Percentage (%)',
          data: scores.length ? scores : [0],
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139, 92, 246, 0.12)',
          fill: true,
          tension: 0.35,
          pointRadius: 5,
          pointBackgroundColor: '#8b5cf6'
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            grid: { color: '#f1f5f9' }
          }
        }
      }
    });
  }
};

window.renderAdminDashboardCharts = function (data) {
  // 1. Difficulty Breakdown Doughnut Chart
  const diffCtx = document.getElementById('adminDifficultyChart');
  if (diffCtx && data.difficulty_breakdown) {
    new Chart(diffCtx, {
      type: 'doughnut',
      data: {
        labels: ['Easy', 'Medium', 'Hard'],
        datasets: [{
          data: [
            data.difficulty_breakdown.Easy || 0,
            data.difficulty_breakdown.Medium || 0,
            data.difficulty_breakdown.Hard || 0
          ],
          backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' }
        },
        cutout: '68%'
      }
    });
  }

  // 2. Category Distribution Bar Chart
  const catCtx = document.getElementById('adminCategoryChart');
  if (catCtx && data.category_stats) {
    const labels = data.category_stats.map(c => c.name);
    const counts = data.category_stats.map(c => c.count);

    new Chart(catCtx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Available Questions',
          data: counts,
          backgroundColor: '#2563eb',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: '#f1f5f9' },
            ticks: { stepSize: 1 }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }
};
