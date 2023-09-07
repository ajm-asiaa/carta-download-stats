import requests
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as mdates

def get_github_downloads(user, repo, tag, packages, baseline_downloads=None):
    url = f'https://api.github.com/repos/{user}/{repo}/releases'
    headers = {'Accept': 'application/vnd.github+json'}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f'Error fetching data: {response.status_code}')
        return None

    data = json.loads(response.text)
    release_data = next((r for r in data if r['tag_name'] == tag), None)

    if not release_data:
        print(f"Error: tag '{tag}' not found")
        return None

    downloads = {
        package: next((asset['download_count'] for asset in release_data['assets'] if asset['name'] == package), 0)
        for package in packages
    }

    if baseline_downloads:
        for package, baseline in baseline_downloads.items():
            if package in downloads:
                downloads[package] += baseline

    return downloads

def update_data_file(user, repo, tag, packages, data_file, baseline_downloads=None):
    downloads = get_github_downloads(user, repo, tag, packages, baseline_downloads)
    if not downloads:
        return None

    if not os.path.exists(data_file):
        with open(data_file, 'w') as f:
            f.write('Date,' + ','.join(packages) + '\n')

    with open(data_file, 'a') as f:
        f.write(f'{pd.Timestamp.now().date()},' + ','.join([str(downloads[package]) for package in packages]) + '\n')

    return pd.read_csv(data_file)


def plot_downloads(df, output_file, tag):
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    df = df.last('30D')

    fig, ax = plt.subplots(figsize=(10, 5))
    df.plot(ax=ax, marker='o')

    total_downloads = df.iloc[-1].to_dict()  # get downloads for each package on the latest date
    labels = [f'{l} ({int(total_downloads[l])})' for l in df.columns]
    ax.legend(labels)

    # Calculate statistics for the last day, 7 days, 14 days, and 30 days
    totals = {
        'last day': (df.iloc[-1] - df.iloc[-2]).sum() if len(df) > 1 else 0,
        'last 7 days': (df.iloc[-1] - df.iloc[-7]).sum() if len(df) > 7 else 0,
        'last 14 days': (df.iloc[-1] - df.iloc[-14]).sum() if len(df) > 14 else 0,
        'last 30 days': (df.iloc[-1] - df.iloc[-30]).sum() if len(df) > 30 else 0,

    }
    averages = {
        'last 7 days': totals['last 7 days'] / 7,
        'last 14 days': totals['last 14 days'] / 14,
        'last 30 days': totals['last 30 days'] / 30,
    }

    # Prepare the date string for today
    today_str = pd.Timestamp.now().date().strftime('%Y-%m-%d')

    # Prepare the statistics text
    stats_text = f'{today_str}\n'
    stats_text += f'Number of downloads over:\n'
    stats_text += f"last day: {int(totals['last day'])}\n"
    for period in ['last 7 days', 'last 14 days', 'last 30 days']:
        stats_text += f"{period}: {int(totals[period])} (average {averages[period]:.1f})\n"

    # Display the statistics in the plot
    ax.text(0.75, 0.25, stats_text, transform=ax.transAxes, horizontalalignment='left', verticalalignment='center')

    ax.set_ylabel('Downloads')
    ax.set_title(f'{tag} cartavis/carta standalone package downloads: {df.iloc[-1].sum()}')

    # Set the y-axis to display integer tick labels
    def integer_formatter(x, pos):
        return f"{int(x):,}"

    ax.yaxis.set_major_formatter(FuncFormatter(integer_formatter))


    # Set the x-axis limits and scale
    ax.set_xlim(df.index.min(), df.index.max() + pd.DateOffset(days=1))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45, ha='right')

    fig.tight_layout()
    fig.savefig(output_file)

def main():
    # v4.0.0 tag
    user = 'cartavis'
    repo = 'carta'
    tag = 'v4.0.0'
    packages = ['CARTA-v4.0.0-arm64.dmg', 'CARTA-v4.0.0-x64.dmg', 'carta.AppImage.aarch64.tgz', 'carta.AppImage.x86_64.tgz']
    data_file = '/var/www/stats/v4-download-stats.csv'
    plot_file = '/var/www/stats/v4-download-plot.png'

    df = update_data_file(user, repo, tag, packages, data_file)
    if df is not None:
        plot_downloads(df, plot_file, tag)
    print("v4 plot updated")

    # v4.0.0-beta.1 tag
    user = 'cartavis'
    repo = 'carta'
    tag = 'v4.0.0-beta.1'
    packages = ['CARTA-v4.0.0-beta.1-arm64.dmg', 'CARTA-v4.0.0-beta.1-x64.dmg', 'carta.AppImage.v4.0.0-beta.1.aarch64.tgz', 'carta.AppImage.v4.0.0-beta.1.x86_64.tgz']
    data_file = '/var/www/stats/v4b1-download-stats.csv'
    plot_file = '/var/www/stats/v4b1-download-plot.png'

    df = update_data_file(user, repo, tag, packages, data_file)
    if df is not None:
        plot_downloads(df, plot_file, tag)
    print("v4b1 plot updated")

    # v3.0.0 tag
    user = 'cartavis'
    repo = 'carta'
    tag = 'v3.0.0'
    packages = ['CARTA-v3.0-M1.dmg', 'CARTA-v3.0-Intel.dmg', 'carta.AppImage.aarch64.tgz', 'carta.AppImage.x86_64.tgz', 'carta-3.0.1-x86_64.AppImage']
    # To compensate for the reset when we added v3.0.1
    baseline_downloads = {
      'CARTA-v3.0-M1.dmg': 389,
      'CARTA-v3.0-Intel.dmg': 447,
      'carta.AppImage.aarch64.tgz': 43,
      'carta.AppImage.x86_64.tgz': 599,
      'carta-3.0.1-x86_64.AppImage': 59
    }
    data_file = '/var/www/stats/v3-download-stats.csv'
    plot_file = '/var/www/stats/v3-download-plot.png'


    df = update_data_file(user, repo, tag, packages, data_file, baseline_downloads)
    if df is not None:
        plot_downloads(df, plot_file, tag)
    print("v3 plot updated")

if __name__ == '__main__':
    main()
