// ============================================
// CHART.JS - Estadísticas del Panel Admin
// ============================================

// Esperar a que el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Obtener datos desde los data attributes
    const salesCanvas = document.getElementById('salesChart');
    const categoryCanvas = document.getElementById('categoryChart');
    const statusCanvas = document.getElementById('statusChart');

    // ==========================================
    // GRÁFICO DE VENTAS POR MES (Líneas)
    // ==========================================
    if (salesCanvas) {
        const salesData = JSON.parse(salesCanvas.dataset.labels || '[]');
        const salesRevenue = JSON.parse(salesCanvas.dataset.revenue || '[]');

        const salesCtx = salesCanvas.getContext('2d');
        new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: salesData,
                datasets: [{
                    label: 'Ingresos ($)',
                    data: salesRevenue,
                    borderColor: '#9a5f28',
                    backgroundColor: 'rgba(154, 95, 40, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#9a5f28',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Ingresos: $' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            }
                        }
                    }
                }
            }
        });
    }

    // ==========================================
    // GRÁFICO DE INGRESOS POR CATEGORÍA (Donut)
    // ==========================================
    if (categoryCanvas) {
        const categoryLabels = JSON.parse(categoryCanvas.dataset.labels || '[]');
        const categoryRevenue = JSON.parse(categoryCanvas.dataset.revenue || '[]');

        const categoryCtx = categoryCanvas.getContext('2d');
        new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: categoryLabels,
                datasets: [{
                    data: categoryRevenue,
                    backgroundColor: [
                        '#9a5f28',
                        '#b87333',
                        '#6b3410',
                        '#3d1d08',
                        '#f9ebd9',
                        '#d4a574'
                    ],
                    borderWidth: 3,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': $' + context.parsed.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
    }

    // ==========================================
    // GRÁFICO DE ESTADOS DE PEDIDOS (Barras)
    // ==========================================
    if (statusCanvas) {
        const statusLabels = JSON.parse(statusCanvas.dataset.labels || '[]');
        const statusCounts = JSON.parse(statusCanvas.dataset.counts || '[]');

        const statusCtx = statusCanvas.getContext('2d');
        new Chart(statusCtx, {
            type: 'bar',
            data: {
                labels: statusLabels,
                datasets: [{
                    label: 'Cantidad de Pedidos',
                    data: statusCounts,
                    backgroundColor: [
                        '#fbbf24',  // pending_payment
                        '#fbbf24',  // pending
                        '#3b82f6',  // paid
                        '#8b5cf6',  // preparing
                        '#6366f1',  // shipped
                        '#10b981',  // delivered
                        '#059669',  // completed
                        '#ef4444'   // cancelled
                    ],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
});