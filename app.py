from flask import Flask, render_template, request, session
import pandas as pd
import markdown2
import pickle
from functools import lru_cache
from collections import defaultdict
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Load data and model
data = pd.read_csv('encyclopedia_updated.csv')

with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

search_counts = defaultdict(int)

@lru_cache(maxsize=128)
def get_package_info(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code == 200:
        info = response.json()['info']
        description = info['description'] or info['summary']
        html_description = markdown2.markdown(description)
        category = model.predict([description])[0]
        return {
            'name': info['name'],
            'version': info['version'],
            'summary': f"Category: {category}",
            'description': html_description,
            'homepage': info['home_page'],
            'predicted_category': category,
            'source': 'pypi'
        }
    return None

@app.route('/')
def home():
    recent = session.get('recent_searches', [])
    return render_template('index.html', recent=recent)

@app.route('/library', methods=['GET', 'POST'])
def library_search():
    from difflib import get_close_matches
    info = None
    if request.method == 'POST':
        query = request.form['query'].strip()
        search_counts[query.lower()] += 1

        # Update recent search history in session
        recent = session.get('recent_searches', [])
        if query not in recent:
            recent.insert(0, query)
            if len(recent) > 5:
                recent = recent[:5]
            session['recent_searches'] = recent

        local = data[data['title'].str.lower() == query.lower()]
        if not local.empty:
            row = local.iloc[0]
            content_html = markdown2.markdown(row['content'])
            info = {
                'name': row['title'],
                'version': 'N/A',
                'summary': f"Category: {row['category']}",
                'description': content_html,
                'homepage': '#',
                'predicted_category': row['category'],
                'source': 'local'
            }
        else:
            suggestions = get_close_matches(query.lower(), data['title'].str.lower(), n=1, cutoff=0.6)
            if suggestions:
                info = {
                    'name': suggestions[0],
                    'version': 'N/A',
                    'summary': 'Did you mean this?',
                    'description': 'Try this suggested name in search.',
                    'homepage': '#',
                    'predicted_category': 'Unknown',
                    'source': 'suggestion'
                }
            else:
                info = get_package_info(query)
    return render_template('library.html', info=info)

@app.route('/category', methods=['GET', 'POST'])
def category_search():
    results = []
    page = int(request.args.get('page', 1))
    per_page = 5

    if request.method == 'POST':
        category = request.form['category'].strip().lower()
        matched = data[data['category'].str.lower() == category]
        results = matched.to_dict(orient='records')
        for item in results:
            item['content'] = markdown2.markdown(item['content'])

        start = (page - 1) * per_page
        end = start + per_page
        paginated = results[start:end]
        total_pages = (len(results) + per_page - 1) // per_page

        return render_template('category.html', results=paginated, category=category, page=page, total_pages=total_pages)

    return render_template('category.html', results=[], page=1, total_pages=1)

@app.route('/analytics')
def analytics():
    import plotly.graph_objs as go
    from plotly.offline import plot

    fallback_data = {
        'Pandas': 5,
        'Numpy': 4,
        'Matplotlib': 3,
        'Flask': 2,
        'TensorFlow': 1
    }

    if not search_counts:
        top = sorted(fallback_data.items(), key=lambda x: x[1], reverse=True)
        is_fallback = True
    else:
        top = sorted(search_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        is_fallback = False

    labels, values = zip(*top)
    fig = go.Figure([go.Bar(x=labels, y=values)])
    fig.update_layout(
        title="Top 10 Most Searched Libraries",
        xaxis_title="Library",
        yaxis_title="Search Count",
        updatemenus=[{
            "buttons": [
                {
                    "args": ["toImage", {"format": "png"}],
                    "label": "📷 Download PNG",
                    "method": "relayout"
                }
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 10},
            "showactive": False,
            "type": "buttons",
            "x": 0.0,
            "xanchor": "left",
            "y": 1.2,
            "yanchor": "top"
        }]
    )
    graph_div = plot(fig, output_type='div', include_plotlyjs=True)

    return render_template("analytics.html", graph_div=graph_div, is_fallback=is_fallback)

if __name__ == '__main__':
    app.run(debug=True)
