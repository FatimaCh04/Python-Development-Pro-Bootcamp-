const balance = document.getElementById('balance');
const incomeTotal = document.getElementById('income-total');
const expenseTotal = document.getElementById('expense-total');
const list = document.getElementById('list');
const form = document.getElementById('transaction-form');
const text = document.getElementById('text');
const amount = document.getElementById('amount');
const category = document.getElementById('category');

// Local Storage
const localStorageTransactions = JSON.parse(localStorage.getItem('transactions'));
let transactions = localStorage.getItem('transactions') !== null ? localStorageTransactions : [];

// Chart Instance
let expenseChart;

// Format Currency
function formatCurrency(num) {
    return '$' + Math.abs(num).toFixed(2);
}

// Add Transaction
function addTransaction(e) {
    e.preventDefault();

    if (text.value.trim() === '' || amount.value.trim() === '') {
        alert('Please add a description and amount');
        return;
    }

    const transaction = {
        id: generateID(),
        text: text.value,
        amount: +amount.value,
        category: amount.value < 0 ? category.value : 'income'
    };

    transactions.push(transaction);
    addTransactionDOM(transaction);
    updateValues();
    updateLocalStorage();
    updateChart();

    text.value = '';
    amount.value = '';
}

// Generate random ID
function generateID() {
    return Math.floor(Math.random() * 100000000);
}

// Add transaction to DOM
function addTransactionDOM(transaction) {
    const sign = transaction.amount < 0 ? '-' : '+';
    const item = document.createElement('li');

    item.classList.add(transaction.amount < 0 ? 'minus' : 'plus');

    item.innerHTML = `
        <div class="details">
            <span>${transaction.text}</span>
            <span class="category">${transaction.category}</span>
        </div>
        <span class="amount">${sign}${formatCurrency(transaction.amount)}</span>
        <button class="delete-btn" onclick="removeTransaction(${transaction.id})"><i class="fa-solid fa-trash"></i></button>
    `;

    list.appendChild(item);
}

// Update balance, income and expense
function updateValues() {
    const amounts = transactions.map(transaction => transaction.amount);
    
    const total = amounts.reduce((acc, item) => (acc += item), 0).toFixed(2);
    
    const income = amounts
        .filter(item => item > 0)
        .reduce((acc, item) => (acc += item), 0)
        .toFixed(2);
        
    const expense = (amounts
        .filter(item => item < 0)
        .reduce((acc, item) => (acc += item), 0) * -1)
        .toFixed(2);

    balance.innerText = total < 0 ? `-$${Math.abs(total).toFixed(2)}` : `$${total}`;
    incomeTotal.innerText = `+${formatCurrency(income)}`;
    expenseTotal.innerText = `-${formatCurrency(expense)}`;
}

// Remove transaction
window.removeTransaction = function(id) {
    transactions = transactions.filter(transaction => transaction.id !== id);
    updateLocalStorage();
    init();
}

// Update local storage
function updateLocalStorage() {
    localStorage.setItem('transactions', JSON.stringify(transactions));
}

// Initialize Chart
function initChart() {
    const ctx = document.getElementById('expenseChart').getContext('2d');
    
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', sans-serif";

    expenseChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#b53cff', // purple
                    '#00f0ff', // blue
                    '#10b981', // green
                    '#ef4444', // red
                    '#f59e0b', // orange
                    '#6366f1'  // indigo
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                    }
                }
            }
        }
    });
}

// Update Chart Data
function updateChart() {
    const expenses = transactions.filter(t => t.amount < 0);
    
    // Group by category
    const categoryTotals = expenses.reduce((acc, curr) => {
        acc[curr.category] = (acc[curr.category] || 0) + Math.abs(curr.amount);
        return acc;
    }, {});

    const labels = Object.keys(categoryTotals).map(c => c.charAt(0).toUpperCase() + c.slice(1));
    const data = Object.values(categoryTotals);

    if(data.length === 0) {
        // Show empty state
        expenseChart.data.labels = ['No Expenses Yet'];
        expenseChart.data.datasets[0].data = [1];
        expenseChart.data.datasets[0].backgroundColor = ['rgba(255,255,255,0.05)'];
    } else {
        expenseChart.data.labels = labels;
        expenseChart.data.datasets[0].data = data;
        expenseChart.data.datasets[0].backgroundColor = [
            '#b53cff', '#00f0ff', '#10b981', '#ef4444', '#f59e0b', '#6366f1'
        ];
    }
    
    expenseChart.update();
}

// Init App
function init() {
    list.innerHTML = '';
    transactions.forEach(addTransactionDOM);
    updateValues();
    
    if(!expenseChart) {
        initChart();
    }
    updateChart();
}

init();

form.addEventListener('submit', addTransaction);
