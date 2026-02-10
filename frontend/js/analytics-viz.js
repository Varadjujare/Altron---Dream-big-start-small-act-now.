/**
 * Advanced Analytics Visualization Module
 * Handles heatmap calendar, Chart.js charts, correlations, and export functionality
 */

// ============================================
// HEATMAP CALENDAR (GitHub-style)
// ============================================

async function renderHeatmapCalendar(year) {
    const container = document.getElementById('heatmapContainer');
    if (!container) return;
    
    // Fetch heatmap data
    const result = await API.get(`/api/analytics/heatmap?year=${year}`);
    if (!result.success) {
        container.innerHTML = '<p class="text-error">Failed to load heatmap data</p>';
        return;
    }
    
    // Create data map for quick lookup
    const dataMap = {};
    result.data.forEach(d => {
        dataMap[d.date] = d;
    });
    
    // Generate calendar grid
    const startDate = new Date(year, 0, 1);
    const endDate = new Date(year, 11, 31);
    
    // Find the first Monday before or on Jan 1
    let currentDate = new Date(startDate);
    while (currentDate.getDay() !== 1) {
        currentDate.setDate(currentDate.getDate() - 1);
    }
    
    let html = '<div class="heatmap-wrapper">';
    html += `<div class="heatmap-header"><h4>Activity in ${year}</h4><div class="heatmap-legend"><span>Less</span><div class="heatmap-cell level-0"></div><div class="heatmap-cell level-1"></div><div class="heatmap-cell level-2"></div><div class="heatmap-cell level-3"></div><div class="heatmap-cell level-4"></div><span>More</span></div></div>`;
    html += '<div class="heatmap-grid">';
    
    // Create cells for entire year (approx 52-53 weeks)
    let weekCount = 0;
    while (currentDate <= endDate || currentDate.getFullYear() === year) {
        for (let day = 0; day < 7; day++) {
            const dateStr = currentDate.toISOString().split('T')[0];
            const data = dataMap[dateStr];
            const level = data ? getHeatmapLevel(data.percentage) : 0;
            const tooltipText = data 
                ? `${dateStr}: ${data.completed}/${data.total} habits (${data.percentage}%)`
                : `${dateStr}: No data`;
            
            html += `<div class="heatmap-cell level-${level}" data-date="${dateStr}" data-tooltip="${tooltipText}"></div>`;
            currentDate.setDate(currentDate.getDate() + 1);
        }
        weekCount++;
        
        // Stop after crossing into next year and completing the week
        if (currentDate.getFullYear() > year && weekCount > 52) break;
    }
    
    html += '</div></div>';
    container.innerHTML = html;
    
    // Add tooltip handlers
    addHeatmapTooltips();
}

function getHeatmapLevel(percentage) {
    if (percentage === 0) return 0;
    if (percentage <= 25) return 1;
    if (percentage <= 50) return 2;
    if (percentage <= 75) return 3;
    return 4;
}

function addHeatmapTooltips() {
    const cells = document.querySelectorAll('.heatmap-cell');
    const tooltip = document.createElement('div');
    tooltip.className = 'heatmap-tooltip';
    document.body.appendChild(tooltip);
    
    cells.forEach(cell => {
        cell.addEventListener('mouseenter', (e) => {
            const text = cell.getAttribute('data-tooltip');
            tooltip.textContent = text;
            tooltip.style.display = 'block';
        });
        
        cell.addEventListener('mousemove', (e) => {
            tooltip.style.left = e.pageX + 10 + 'px';
            tooltip.style.top = e.pageY + 10 + 'px';
        });
        
        cell.addEventListener('mouseleave', () => {
            tooltip.style.display = 'none';
        });
    });
}

// ============================================
// PRODUCTIVITY SCORE CHART (Chart.js)
// ============================================

let productivityChart = null;

async function renderProductivityChart(period = 'month') {
    const canvas = document.getElementById('productivityChart');
    if (!canvas) return;
    
    const result = await API.get(`/api/analytics/productivity-score?period=${period}`);
    if (!result.success) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if exists
    if (productivityChart) {
        productivityChart.destroy();
    }
    
    const scores = result.scores;
    const labels = scores.map(s => {
        const date = new Date(s.date);
        return period === 'week' ? date.toLocaleDateString('en-US', {weekday: 'short'}) : date.toLocaleDateString('en-US', {month: 'short', day: 'numeric'});
    });
    
    productivityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Productivity Score',
                    data: scores.map(s => s.score),
                    borderColor: '#26a641',
                    backgroundColor: 'rgba(38, 166, 65, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Habit Score',
                    data: scores.map(s => s.habits_score),
                    borderColor: '#39d353',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    tension: 0.4
                },
                {
                    label: 'Task Score',
                    data: scores.map(s => s.tasks_score),
                    borderColor: '#0969da',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--text-primary'),
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary'),
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary'),
                        maxRotation: 45,
                        minRotation: 0
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ============================================
// HABIT STRENGTH VISUALIZATION
// ============================================

async function renderHabitStrength() {
    const container = document.getElementById('habitStrengthContainer');
    if (!container) return;
    
    const result = await API.get('/api/analytics/habit-strength');
    if (!result.success) {
        container.innerHTML = '<p class="text-error">Failed to load habit strength data</p>';
        return;
    }
    
    if (result.habits.length === 0) {
        container.innerHTML = '<p class="text-muted">No habits to analyze yet. Start tracking some habits!</p>';
        return;
    }
    
    let html = '<div class="habit-strength-list">';
    
    result.habits.forEach(habit => {
        const scoreColor = habit.consistency_score >= 70 ? 'success' : habit.consistency_score >= 40 ? 'warning' : 'error';
        
        html += `
            <div class="habit-strength-item">
                <div class="habit-strength-header">
                    <h4 class="habit-strength-name">${habit.habit_name}</h4>
                    <span class="badge badge-${scoreColor}">${habit.consistency_score}/100</span>
                </div>
                <div class="habit-strength-metrics">
                    <div class="metric">
                        <span class="metric-label">Completion Rate</span>
                        <div class="metric-bar-wrapper">
                            <div class="metric-bar" style="width: ${habit.completion_rate}%"></div>
                        </div>
                        <span class="metric-value">${habit.completion_rate}%</span>
                    </div>
                    <div class="metric-stats">
                        <div class="metric-stat">
                            <span class="metric-stat-icon">🔥</span>
                            <span class="metric-stat-value">${habit.current_streak}</span>
                            <span class="metric-stat-label">Current</span>
                        </div>
                        <div class="metric-stat">
                            <span class="metric-stat-icon">🏆</span>
                            <span class="metric-stat-value">${habit.best_streak}</span>
                            <span class="metric-stat-label">Best</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// ============================================
// CORRELATION MATRIX
// ============================================

async function renderCorrelationMatrix() {
    const container = document.getElementById('correlationContainer');
    if (!container) return;
    
    const result = await API.get('/api/analytics/correlations');
    if (!result.success) {
        container.innerHTML = '<p class="text-error">Failed to load correlation data</p>';
        return;
    }
    
    if (result.correlations.length === 0) {
        container.innerHTML = '<p class="text-muted">' + (result.message || 'No correlation data available') + '</p>';
        return;
    }
    
    // Show top 10 correlations
    const topCorrelations = result.correlations.slice(0, 10);
    
    let html = '<div class="correlation-list">';
    
    topCorrelations.forEach(corr => {
        const percentage = Math.round(corr.correlation * 100);
        const level = getCorrelationLevel(corr.correlation);
        
        html += `
            <div class="correlation-item">
                <div class="correlation-habits">
                    <span class="correlation-habit">${corr.habit1}</span>
                    <span class="correlation-arrow">↔️</span>
                    <span class="correlation-habit">${corr.habit2}</span>
                </div>
                <div class="correlation-bar-wrapper">
                    <div class="correlation-bar level-${level}" style="width: ${percentage}%"></div>
                </div>
                <span class="correlation-value">${percentage}%</span>
            </div>
        `;
    });
    
    html += '</div>';
    html += `<p class="text-muted text-sm mt-md">Analysis based on last ${result.analysis_period} days</p>`;
    container.innerHTML = html;
}

function getCorrelationLevel(correlation) {
    if (correlation >= 0.7) return 4;
    if (correlation >= 0.5) return 3;
    if (correlation >= 0.3) return 2;
    if (correlation > 0) return 1;
    return 0;
}

// ============================================
// COMPARISON CHARTS (Chart.js)
// ============================================

let comparisonChart = null;

async function renderComparisonChart() {
    const canvas = document.getElementById('comparisonChart');
    if (!canvas) return;
    
    const result = await API.get('/api/analytics/comparison');
    if (!result.success) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (comparisonChart) {
        comparisonChart.destroy();
    }
    
    const period1 = result.period1;
    const period2 = result.period2;
    
    comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Habits Completed', 'Tasks Completed'],
            datasets: [
                {
                    label: `${period1.month_name} ${period1.year}`,
                    data: [period1.habits_completed, period1.tasks_completed],
                    backgroundColor: '#26a641',
                    borderRadius: 8
                },
                {
                    label: `${period2.month_name} ${period2.year}`,
                    data: [period2.habits_completed, period2.tasks_completed],
                    backgroundColor: '#6e7681',
                    borderRadius: 8
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--text-primary'),
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            if (context.datasetIndex === 0) {
                                const change = context.dataIndex === 0 ? result.comparison.habits_change : result.comparison.tasks_change;
                                const icon = change >= 0 ? '↑' : '↓';
                                const color = change >= 0 ? 'green' : 'red';
                                return `${icon} ${Math.abs(change)}% vs previous month`;
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary')
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary')
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
    
    // Display percentage changes
    const changesContainer = document.getElementById('comparisonChanges');
    if (changesContainer) {
        const habitsChange = result.comparison.habits_change;
        const tasksChange = result.comparison.tasks_change;
        
        changesContainer.innerHTML = `
            <div class="comparison-changes">
                <div class="change-item ${habitsChange >= 0 ? 'positive' : 'negative'}">
                    <span class="change-label">Habits</span>
                    <span class="change-value">${habitsChange >= 0 ? '↑' : '↓'} ${Math.abs(habitsChange)}%</span>
                </div>
                <div class="change-item ${tasksChange >= 0 ? 'positive' : 'negative'}">
                    <span class="change-label">Tasks</span>
                    <span class="change-value">${tasksChange >= 0 ? '↑' : '↓'} ${Math.abs(tasksChange)}%</span>
                </div>
            </div>
        `;
    }
}

// ============================================
// EXPORT FUNCTIONALITY
// ============================================

async function exportToCSV() {
    const exportBtn = document.getElementById('exportCSVBtn');
    if (exportBtn) exportBtn.disabled = true;
    
    try {
        // Get date range (last 30 days by default)
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);
        
        const result = await API.get(`/api/analytics/export-data?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}`);
        
        if (!result.success) {
            Toast.error('Failed to export data');
            return;
        }
        
        // Build CSV content
        let csv = 'Date,Type,Name,Status,Priority\n';
        
        // Add habit logs
        result.habit_logs.forEach(log => {
            csv += `${log.date},Habit,"${log.habit_name}",${log.status},N/A\n`;
        });
        
        // Add tasks
        result.tasks.forEach(task => {
            csv += `${task.date},Task,"${task.title}",${task.status},${task.priority}\n`;
        });
        
        // Download CSV
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `lifesync-export-${endDate.toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        Toast.success('CSV exported successfully!');
    } catch (error) {
        Toast.error('Export failed: ' + error.message);
    } finally {
        if (exportBtn) exportBtn.disabled = false;
    }
}

async function exportToPDF() {
    const exportBtn = document.getElementById('exportPDFBtn');
    if (exportBtn) exportBtn.disabled = true;
    
    try {
        Toast.info('Generating PDF report...');
        
        // Get data for PDF
        const [heatmapData, strengthData, correlationData, productivityData] = await Promise.all([
            API.get(`/api/analytics/heatmap?year=${new Date().getFullYear()}`),
            API.get('/api/analytics/habit-strength'),
            API.get('/api/analytics/correlations'),
            API.get('/api/analytics/productivity-score?period=month')
        ]);
        
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        // Title
        doc.setFontSize(20);
        doc.setTextColor(38, 166, 65);
        doc.text('LifeSync Productivity Report', 14, 20);
        
        // Date range
        doc.setFontSize(10);
        doc.setTextColor(100, 100, 100);
        doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 14, 28);
        
        // Summary Statistics
        doc.setFontSize(14);
        doc.setTextColor(0, 0, 0);
        doc.text('Summary Statistics', 14, 40);
        
        if (strengthData.success && strengthData.habits.length > 0) {
            doc.setFontSize(10);
            const tableData = strengthData.habits.map(h => [
                h.habit_name,
                h.completion_rate + '%',
                h.current_streak.toString(),
                h.best_streak.toString(),
                h.consistency_score.toString()
            ]);
            
            doc.autoTable({
                startY: 45,
                head: [['Habit', 'Completion Rate', 'Current Streak', 'Best Streak', 'Consistency Score']],
                body: tableData,
                theme: 'grid',
                headStyles: { fillColor: [38, 166, 65] },
                styles: { fontSize: 9 }
            });
        }
        
        // Correlations
        let yPos = doc.lastAutoTable ? doc.lastAutoTable.finalY + 15 : 80;
        if (yPos > 250) {
            doc.addPage();
            yPos = 20;
        }
        
        doc.setFontSize(14);
        doc.text('Habit Correlations', 14, yPos);
        
        if (correlationData.success && correlationData.correlations.length > 0) {
            const corrTable = correlationData.correlations.slice(0, 10).map(c => [
                c.habit1,
                c.habit2,
                Math.round(c.correlation * 100) + '%'
            ]);
            
            doc.autoTable({
                startY: yPos + 5,
                head: [['Habit 1', 'Habit 2', 'Correlation']],
                body: corrTable,
                theme: 'grid',
                headStyles: { fillColor: [38, 166, 65] },
                styles: { fontSize: 9 }
            });
        }
        
        // Productivity Scores Summary
        yPos = doc.lastAutoTable ? doc.lastAutoTable.finalY + 15 : yPos + 40;
        if (yPos > 250) {
            doc.addPage();
            yPos = 20;
        }
        
        doc.setFontSize(14);
        doc.text('Productivity Trends', 14, yPos);
        
        if (productivityData.success && productivityData.scores.length > 0) {
            const avgScore = productivityData.scores.reduce((sum, s) => sum + s.score, 0) / productivityData.scores.length;
            doc.setFontSize(10);
            doc.text(`Average Productivity Score (30 days): ${avgScore.toFixed(1)}%`, 14, yPos + 7);
        }
        
        // Footer
        const pageCount = doc.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
            doc.setPage(i);
            doc.setFontSize(8);
            doc.setTextColor(150, 150, 150);
            doc.text(`Page ${i} of ${pageCount}`, doc.internal.pageSize.width / 2, doc.internal.pageSize.height - 10, { align: 'center' });
        }
        
        // Save PDF
        doc.save(`lifesync-report-${new Date().toISOString().split('T')[0]}.pdf`);
        
        Toast.success('PDF exported successfully!');
    } catch (error) {
        console.error('PDF export error:', error);
        Toast.error('PDF export failed: ' + error.message);
    } finally {
        if (exportBtn) exportBtn.disabled = false;
    }
}

// ============================================
// INITIALIZATION
// ============================================

async function initAdvancedAnalytics() {
    const currentYear = new Date().getFullYear();
    
    // Load all visualizations
    await Promise.all([
        renderHeatmapCalendar(currentYear),
        renderProductivityChart('month'),
        renderHabitStrength(),
        renderCorrelationMatrix(),
        renderComparisonChart()
    ]);
}

// Period selector for productivity chart
function changePeriod(period) {
    renderProductivityChart(period);
    
    // Update active button
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.period === period);
    });
}
