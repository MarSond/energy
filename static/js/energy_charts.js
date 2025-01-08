// energy_charts.js

let charts = {};
let currentEnergyType = '';
let globalData = {};

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    setupTabListeners();
    initializeCharts();
});

function setupTabListeners() {
    const energyTabs = document.querySelectorAll('#energyTabs button');
    console.log(`Found ${energyTabs.length} energy tabs`);
    
    energyTabs.forEach(tab => {
        tab.addEventListener('click', function (event) {
            console.log(`Tab clicked: ${event.target.id}`);
            const energyType = event.target.id.replace('-tab', '');
            switchToEnergyType(energyType);
        });
    });
}

function switchToEnergyType(energyType) {
    console.log(`Switching to energy type: ${energyType}`);
    currentEnergyType = energyType;
    if (globalData[energyType]) {
        console.log(`Using cached data for ${energyType}`);
        createAllCharts(energyType, globalData[energyType]);
    } else {
        console.log(`Fetching new data for ${energyType}`);
        fetchDataAndCreateCharts(energyType);
    }
}

function initializeCharts() {
    const activeTab = document.querySelector('#energyTabs button.active');
    if (activeTab) {
        console.log(`Initializing charts for active tab: ${activeTab.id}`);
        const initialEnergyType = activeTab.id.replace('-tab', '');
        switchToEnergyType(initialEnergyType);
    } else {
        console.error('No active tab found');
    }
}

function fetchDataAndCreateCharts(energyType) {
    console.log(`Fetching data for ${energyType}`);
    fetch(`/api/data/${energyType}`)
        .then(response => response.json())
        .then(data => {
            console.log(`Received data for ${energyType}:`, data);
            globalData[energyType] = data;
            createAllCharts(energyType, data);
        })
        .catch(error => console.error('Error fetching data:', error));
}

function createAllCharts(energyType, data) {
    console.log(`Creating all charts for ${energyType}`);
    createYearlyChart(energyType, data);
    createMonthlyChart(energyType, data);
    createAvgMonthlyChart(energyType, data);
    createCumulativeChart(energyType, data);
}

function createChart(chartId, config) {
    console.log(`Creating/updating chart: ${chartId}`);
    const ctx = document.getElementById(chartId);
    if (!ctx) {
        console.error(`Canvas element with id ${chartId} not found`);
        return;
    }
    
    if (charts[chartId]) {
        console.log(`Destroying existing chart: ${chartId}`);
        charts[chartId].destroy();
    }
    
    console.log(`Creating new chart: ${chartId}`);
    charts[chartId] = new Chart(ctx, config);
}

function createYearlyChart(energyType, data) {
    console.log(`Creating yearly chart for ${energyType}`);
    const yearlyData = processYearlyData(data);
    const config = {
        type: 'bar',
        data: {
            labels: yearlyData.labels,
            datasets: [{
                label: 'Jährlicher Verbrauch',
                data: yearlyData.values,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Verbrauch'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `Jährlicher ${energyType.charAt(0).toUpperCase() + energyType.slice(1)}-Verbrauch`
                }
            }
        }
    };
    createChart(`${energyType}-yearly-chart`, config);
}

function createMonthlyChart(energyType, data) {
    console.log(`Creating monthly chart for ${energyType}`);
    const monthlyData = processMonthlyData(data);
    const config = {
        type: 'line',
        data: {
            labels: monthlyData.labels,
            datasets: monthlyData.datasets
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Verbrauch'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `Monatlicher ${energyType.charAt(0).toUpperCase() + energyType.slice(1)}-Verbrauch (Letzte 3 Jahre)`
                }
            }
        }
    };
    createChart(`${energyType}-monthly-chart`, config);
}

function createAvgMonthlyChart(energyType, data) {
    console.log(`Creating average monthly chart for ${energyType}`);
    const avgMonthlyData = processAvgMonthlyData(data);
    const config = {
        type: 'bar',
        data: {
            labels: avgMonthlyData.labels,
            datasets: [{
                label: 'Durchschnittlicher Verbrauch',
                data: avgMonthlyData.values,
                backgroundColor: 'rgba(153, 102, 255, 0.6)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Durchschnittlicher Verbrauch'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `Durchschnittlicher monatlicher ${energyType.charAt(0).toUpperCase() + energyType.slice(1)}-Verbrauch`
                }
            }
        }
    };
    createChart(`${energyType}-avg-monthly-chart`, config);
}

function createCumulativeChart(energyType, data) {
    console.log(`Creating cumulative chart for ${energyType}`);
    const cumulativeData = processCumulativeData(data);
    const config = {
        type: 'line',
        data: {
            labels: cumulativeData.labels,
            datasets: [{
                label: 'Kumulativer Verbrauch',
                data: cumulativeData.values,
                fill: false,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Kumulativer Verbrauch'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `Kumulativer ${energyType.charAt(0).toUpperCase() + energyType.slice(1)}-Verbrauch`
                }
            }
        }
    };
    createChart(`${energyType}-cumulative-chart`, config);
}

// Helper functions to process data
function processYearlyData(data) {
    const yearlyData = {};
    data.labels.forEach((date, index) => {
        const year = date.split('-')[0];
        if (!yearlyData[year]) {
            yearlyData[year] = 0;
        }
        yearlyData[year] += data.values[index];
    });

    const sortedYears = Object.keys(yearlyData).sort();
    return {
        labels: sortedYears,
        values: sortedYears.map(year => yearlyData[year])
    };
}

function processMonthlyData(data) {
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const currentYear = new Date().getFullYear();
    const startYear = currentYear - 2;  // Last 3 years
    
    const monthlyData = {};
    data.labels.forEach((date, index) => {
        const [year, month] = date.split('-').map(Number);
        if (year >= startYear) {
            if (!monthlyData[year]) {
                monthlyData[year] = Array(12).fill(0);
            }
            monthlyData[year][month - 1] += data.values[index];
        }
    });

    const datasets = Object.keys(monthlyData).map(year => ({
        label: year,
        data: monthlyData[year],
        fill: false,
        borderColor: `rgba(${Math.random() * 255},${Math.random() * 255},${Math.random() * 255},1)`,
        tension: 0.1
    }));

    return {
        labels: monthNames,
        datasets: datasets
    };
}

function processAvgMonthlyData(data) {
    const monthlySum = Array(12).fill(0);
    const monthlyCount = Array(12).fill(0);

    data.labels.forEach((date, index) => {
        const month = parseInt(date.split('-')[1]) - 1;
        monthlySum[month] += data.values[index];
        monthlyCount[month]++;
    });

    const avgMonthlyValues = monthlySum.map((sum, index) => 
        monthlyCount[index] > 0 ? sum / monthlyCount[index] : 0
    );

    return {
        labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        values: avgMonthlyValues
    };
}

function processCumulativeData(data) {
    let cumulative = 0;
    const cumulativeValues = data.values.map(value => cumulative += value);

    return {
        labels: data.labels,
        values: cumulativeValues
    };
}

// TODO: Implement functions to update charts based on user selections
function updateTimeRange(chartType, startDate, endDate) {
    // Implementation for updating time range
}

function updateYearlyChart(startYear, endYear) {
    // Implementation for updating yearly chart
}

function updateMonthlyChart(year, startMonth, endMonth) {
    // Implementation for updating monthly chart
}

// TODO: Setup UI controls for time range selection
function setupTimeRangeControls() {
    // Implementation for setting up time range controls
}

// Export functions for potential use in other scripts
window.energyCharts = {
    updateTimeRange,
    updateYearlyChart,
    updateMonthlyChart
};