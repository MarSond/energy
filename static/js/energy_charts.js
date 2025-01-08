// Konfigurationsobjekt für verschiedene Energietypen
const CONFIG = {
    strom: {
        color: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        label: 'Stromverbrauch',
        unit: 'kWh'
    },
    gas: {
        color: 'rgba(255, 159, 64, 0.6)',
        borderColor: 'rgba(255, 159, 64, 1)',
        label: 'Gasverbrauch',
        unit: 'm³'
    },
    wasser: {
        color: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        label: 'Wasserverbrauch',
        unit: 'm³'
    },
    einspeisung: {
        color: 'rgba(153, 102, 255, 0.6)',
        borderColor: 'rgba(153, 102, 255, 1)',
        label: 'Einspeisung',
        unit: 'kWh'
    },
    dle: {
        color: 'rgba(255, 99, 132, 0.6)',
        borderColor: 'rgba(255, 99, 132, 1)',
        label: 'DLE',
        unit: 'Einheit'
    },
    garten: {
        color: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        label: 'Garten',
        unit: 'm³'
    }
};

// Cache für die Daten
let dataCache = new Map();
let charts = new Map();

// Event Listener für DOM Content Loaded
document.addEventListener('DOMContentLoaded', () => {
    setupTabListeners();
    initializeCharts();

    const triggerTabList = [].slice.call(document.querySelectorAll('#energyTabs button'));
    triggerTabList.forEach(function (triggerEl) {
        new bootstrap.Tab(triggerEl);
    });
});

function setupTabListeners() {
    // Bootstrap Tab Events abfangen
    document.querySelectorAll('button[data-bs-toggle="tab"]').forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', event => {
            // Dies wird ausgelöst NACHDEM der Tab gewechselt wurde
            const energyType = event.target.id.replace('-tab', '');
            console.log('Bootstrap Tab switched to:', energyType);
            switchEnergyType(energyType);
        });
    });
}

// Initialisierung der Charts
function initializeCharts() {
    const activeTab = document.querySelector('#energyTabs button.active');
    if (activeTab) {
        const initialType = activeTab.id.replace('-tab', '');
        switchEnergyType(initialType);
    }
}

// Wechsel zwischen Energietypen
async function switchEnergyType(type) {
    console.log('Switching to:', type);
    try {
        if (dataCache.has(type)) {
            dataCache.delete(type);
        }
        const data = await getDataForType(type);
        updateAllCharts(type, data);
    } catch (error) {
        console.error(`Fehler beim Laden der Daten für ${type}:`, error);
        showError(`Fehler beim Laden der ${type}-Daten`);
    }
}

// Daten abrufen (mit Caching)
async function getDataForType(type) {
    try {
        const response = await fetch(`/api/data/${type}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        dataCache.set(type, data);
        return data;
    } catch (error) {
        console.error(`Fehler beim Abrufen der Daten für ${type}:`, error);
        return {
            labels: [],
            values: []
        };
    }
}

// Update aller Charts
function updateAllCharts(type, data) {
    console.log('Updating all charts for:', type);
    const config = CONFIG[type];
    if (!config) {
        console.error(`Keine Konfiguration für Typ ${type} gefunden`);
        return;
    }

    updateYearlyChart(type, data);
    updateMonthlyChart(type, data);
    updateAvgMonthlyChart(type, data);
    updateCumulativeChart(type, data);
}

// Yearly Chart Update
function updateYearlyChart(type, data) {
    const yearlyData = processYearlyData(data);
    const config = createChartConfig('bar', {
        labels: yearlyData.labels,
        datasets: [{
            label: `Jährlicher ${CONFIG[type].label}`,
            data: yearlyData.values,
            backgroundColor: CONFIG[type].color,
            borderColor: CONFIG[type].borderColor,
            borderWidth: 1
        }]
    }, {
        yAxisLabel: CONFIG[type].unit
    });

    updateChart(`${type}-yearly-chart`, config);
}

// Monthly Chart Update
function updateMonthlyChart(type, data) {
    const monthlyData = processMonthlyData(data);
    const config = createChartConfig('line', {
        labels: monthlyData.labels,
        datasets: monthlyData.datasets.map(dataset => ({
            ...dataset,
            borderColor: CONFIG[type].borderColor,
            backgroundColor: CONFIG[type].color
        }))
    }, {
        yAxisLabel: CONFIG[type].unit
    });

    updateChart(`${type}-monthly-chart`, config);
}

// Average Monthly Chart Update
function updateAvgMonthlyChart(type, data) {
    const avgData = processAvgMonthlyData(data);
    const config = createChartConfig('bar', {
        labels: avgData.labels,
        datasets: [{
            label: `Durchschnittlicher ${CONFIG[type].label}`,
            data: avgData.values,
            backgroundColor: CONFIG[type].color,
            borderColor: CONFIG[type].borderColor,
            borderWidth: 1
        }]
    }, {
        yAxisLabel: CONFIG[type].unit
    });

    updateChart(`${type}-avg-monthly-chart`, config);
}

// Cumulative Chart Update
function updateCumulativeChart(type, data) {
    const cumulativeData = processCumulativeData(data);
    const config = createChartConfig('line', {
        labels: cumulativeData.labels,
        datasets: [{
            label: `Kumulativer ${CONFIG[type].label}`,
            data: cumulativeData.values,
            borderColor: CONFIG[type].borderColor,
            backgroundColor: CONFIG[type].color,
            fill: false
        }]
    }, {
        yAxisLabel: CONFIG[type].unit
    });

    updateChart(`${type}-cumulative-chart`, config);
}

// Hilfsfunktion zum Erstellen der Chart-Konfiguration
function createChartConfig(type, data, options = {}) {
    return {
        type,
        data,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: options.yAxisLabel || ''
                    }
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top'
                }
            }
        }
    };
}

// Chart Update Logik
function updateChart(chartId, config) {
    const canvas = document.getElementById(chartId);
    if (!canvas) {
        console.error(`Canvas ${chartId} nicht gefunden`);
        return;
    }

    if (charts.has(chartId)) {
        charts.get(chartId).destroy();
    }

    const ctx = canvas.getContext('2d');
    charts.set(chartId, new Chart(ctx, config));
}

// Datenverarbeitungsfunktionen
function processYearlyData(data) {
    const yearlyData = {};
    data.labels.forEach((date, index) => {
        const year = date.split('-')[0];
        yearlyData[year] = (yearlyData[year] || 0) + (data.values[index] || 0);
    });

    const sortedYears = Object.keys(yearlyData).sort();
    return {
        labels: sortedYears,
        values: sortedYears.map(year => yearlyData[year])
    };
}

function processMonthlyData(data) {
    const monthNames = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"];
    const currentYear = new Date().getFullYear();
    const startYear = currentYear - 2; // Jetzt 3 Jahre
    
    // Feste Farben pro Jahr - jeweils unterschiedlich
    const yearColors = {
        [currentYear]: 'rgb(75, 192, 192)',      // Türkis
        [currentYear - 1]: 'rgb(255, 99, 132)',  // Rot
        [currentYear - 2]: 'rgb(54, 162, 235)'   // Blau

    };
    
    const monthlyData = {};
    data.labels.forEach((date, index) => {
        const [year, month] = date.split('-').map(Number);
        if (year >= startYear) {
            monthlyData[year] = monthlyData[year] || Array(12).fill(0);
            monthlyData[year][month - 1] += data.values[index] || 0;
        }
    });

    return {
        labels: monthNames,
        datasets: Object.entries(monthlyData)
            .sort(([yearA], [yearB]) => yearB - yearA) // Neueste Jahre zuerst
            .map(([year, values]) => ({
                label: year.toString(),
                data: values,
                fill: false,
                borderColor: yearColors[year],
                backgroundColor: yearColors[year],
                tension: 0.1
            }))
    };
}

function processAvgMonthlyData(data) {
    const monthlySum = Array(12).fill(0);
    const monthlyCount = Array(12).fill(0);
    const monthNames = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"];

    data.labels.forEach((date, index) => {
        const month = parseInt(date.split('-')[1]) - 1;
        if (!isNaN(data.values[index])) {
            monthlySum[month] += data.values[index];
            monthlyCount[month]++;
        }
    });

    return {
        labels: monthNames,
        values: monthlySum.map((sum, index) => 
            monthlyCount[index] > 0 ? sum / monthlyCount[index] : 0
        )
    };
}

function processCumulativeData(data) {
    let cumulative = 0;
    const values = [];
    
    data.labels.forEach((_, index) => {
        if (!isNaN(data.values[index])) {
            cumulative += data.values[index];
        }
        values.push(cumulative);
    });

    return {
        labels: data.labels,
        values
    };
}

// Fehlermeldung anzeigen
function showError(message) {
    // Hier könnte eine Funktion zur Anzeige von Fehlermeldungen implementiert werden
    console.error(message);
}