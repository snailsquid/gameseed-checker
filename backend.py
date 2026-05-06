import pandas as pd
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

_mobile_full = None
_pc_full = None
df_all = None


def clean_text(text):
    if pd.isna(text):
        return ""
    return str(text).strip().lower()


def parse_input(text):
    lines = text.strip().split("\n")
    parsed = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Filter out "Anggota" and "Ketua" lines
        lower_line = line.lower()
        if "anggota" in lower_line or "ketua" in lower_line:
            continue
        name = re.split(r'@', line)[0]
        name = re.sub(r'[\-–—]\s*$', '', name).strip()
        if name:
            parsed.append({"original": name, "clean": clean_text(name)})
    return parsed


def try_merge(mobile_path, pc_path):
    global _mobile_full, _pc_full, df_all
    _mobile_full = mobile_path
    _pc_full = pc_path

    if mobile_path and pc_path:
        try:
            df1 = pd.read_csv(mobile_path)
            df2 = pd.read_csv(pc_path)
            df1.columns = df1.columns.str.strip()
            df2.columns = df2.columns.str.strip()
            df1_nama = df1.iloc[:, [4, 19, 29]]
            df1_nama.columns = ['Nama Lengkap', 'Nama Tim', 'Team']
            df2_nama = df2.iloc[:, [4, 19, 29]]
            df2_nama.columns = ['Nama Lengkap', 'Nama Tim', 'Team']
            for df, src in [(df1_nama, 'Mobile'), (df2_nama, 'PC')]:
                df['Nama Asli']  = df['Nama Lengkap']
                df['Nama Clean'] = df['Nama Lengkap'].apply(clean_text)
                df['source']     = src
                df['Team'] = df['Team'].fillna(df['Nama Tim'])
            df1 = df1_nama
            df2 = df2_nama
            df_all = pd.concat([df1, df2], ignore_index=True)
            return {'success': True, 'status': 'ok', 'message': f"{len(df_all)} participants loaded", 'count': len(df_all)}
        except Exception as e:
            return {'success': False, 'status': 'error', 'message': str(e), 'count': 0}
    elif mobile_path:
        try:
            df_mobile = pd.read_csv(mobile_path)
            df_mobile.columns = df_mobile.columns.str.strip()
            df_mobile_nama = df_mobile.iloc[:, [4, 19, 29]].copy()
            df_mobile_nama.columns = ['Nama Lengkap', 'Nama Tim', 'Team']
            df_mobile_nama['Nama Asli'] = df_mobile_nama['Nama Lengkap']
            df_mobile_nama['Nama Clean'] = df_mobile_nama['Nama Lengkap'].apply(clean_text)
            df_mobile_nama['source'] = 'Mobile'
            df_mobile_nama['Team'] = df_mobile_nama['Team'].fillna(df_mobile_nama['Nama Tim'])
            df_all = df_mobile_nama
            mobile_count = len(df_all)
            return {'success': True, 'status': 'partial', 'message': f'Mobile loaded ({mobile_count}) — add PC', 'count': mobile_count}
        except Exception as e:
            return {'success': False, 'status': 'error', 'message': str(e), 'count': 0}
    elif pc_path:
        try:
            df_pc = pd.read_csv(pc_path)
            df_pc.columns = df_pc.columns.str.strip()
            df_pc_nama = df_pc.iloc[:, [4, 19, 29]].copy()
            df_pc_nama.columns = ['Nama Lengkap', 'Nama Tim', 'Team']
            df_pc_nama['Nama Asli'] = df_pc_nama['Nama Lengkap']
            df_pc_nama['Nama Clean'] = df_pc_nama['Nama Lengkap'].apply(clean_text)
            df_pc_nama['source'] = 'PC'
            df_pc_nama['Team'] = df_pc_nama['Team'].fillna(df_pc_nama['Nama Tim'])
            df_all = df_pc_nama
            pc_count = len(df_all)
            return {'success': True, 'status': 'partial', 'message': f'PC loaded ({pc_count}) — add Mobile', 'count': pc_count}
        except Exception as e:
            return {'success': False, 'status': 'error', 'message': str(e), 'count': 0}
    return {'success': False, 'status': 'none', 'message': 'No files loaded', 'count': 0}


def do_check(data):
    global df_all
    results = []

    for item in data:
        match = df_all[df_all['Nama Clean'] == item["clean"]]
        if not match.empty:
            row = match.iloc[0]
            team_values = match['Team'].dropna().unique()
            team = team_values[0] if len(team_values) > 0 else ''
            results.append({
                "name": item["original"],
                "source": ", ".join(match['source'].unique()),
                "team": team,
                "verified": True
            })
        else:
            results.append({
                "name": item["original"],
                "source": "",
                "team": "",
                "verified": False
            })

    total = len(data)
    n_registered = sum(1 for r in results if r["verified"])
    n_not_registered = total - n_registered
    n_mob = sum(1 for r in results if r["verified"] and "Mobile" in r["source"])
    n_pc = sum(1 for r in results if r["verified"] and "PC" in r["source"])

    return {
        'results': results,
        'stats': {
            'total': total,
            'registered_count': n_registered,
            'not_registered_count': n_not_registered,
            'mobile_count': n_mob,
            'pc_count': n_pc
        }
    }


@app.route('/')
def index():
    from flask import render_template
    return render_template('index.html')


@app.route('/api/load-mobile', methods=['POST'])
def load_mobile():
    global _mobile_full
    data = request.json
    _mobile_full = data.get('path')
    result = try_merge(_mobile_full, _pc_full)
    return jsonify(result)


@app.route('/api/load-pc', methods=['POST'])
def load_pc():
    global _pc_full
    data = request.json
    _pc_full = data.get('path')
    result = try_merge(_mobile_full, _pc_full)
    return jsonify(result)


@app.route('/api/check', methods=['POST'])
def check():
    global df_all
    if df_all is None:
        return jsonify({'error': 'No CSV data loaded. Please load Mobile and PC CSV files first.'})
    data = request.json
    names_text = data.get('names', '')
    parsed = parse_input(names_text)
    result = do_check(parsed)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=5000)