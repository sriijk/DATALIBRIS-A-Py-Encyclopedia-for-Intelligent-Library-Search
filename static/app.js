document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    const resultDiv = document.getElementById('result');
    const loading = document.getElementById('loading');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = form.query.value;
        resultDiv.innerHTML = '';
        loading.style.display = 'block';

        const response = await fetch('/api/search', {
            method: 'POST',
            body: new URLSearchParams({ query })
        });

        loading.style.display = 'none';
        const data = await response.json();

        if (data.error) {
            resultDiv.innerHTML = '<p>No results found.</p>';
        } else {
            resultDiv.innerHTML = `
                <h2>${data.name}</h2>
                <p><strong>Category:</strong> ${data.predicted_category}</p>
                <div>${data.description}</div>
            `;
        }
    });
});
