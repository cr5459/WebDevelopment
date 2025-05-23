import pandas as pd
import plotly.express as px
import preswald
from preswald import connect, text, plotly, slider, checkbox, sidebar

connect()

sidebar(
    defaultopen=True,
    logo="images/logoH.png",
    name="Project Himalaya",
)

# Load data
exped_df = pd.read_csv("data/exped.csv")
peaks_df = pd.read_csv("data/peaks.csv")

# Filter top 10 nations
top_nations = exped_df['nation'].value_counts().head(10).index.tolist()
filtered_df = exped_df[exped_df['nation'].isin(top_nations)].copy()

# Filter valid years (exclude years with 0 expeditions)
valid_years = (
    filtered_df['year'].value_counts()
    .sort_index()
    .loc[lambda x: x > 0]
    .index.tolist()
)
min_year = min(valid_years)
max_year = max(valid_years)

# -- Sidebar Layout and Controls --

# -- Header & Intro Text --
text("# Project Himalaya: Basecamp Analytics")
text("## Explore expedition trends from top nations across all time or a specific year.")
preswald.image(src="https://cdn.britannica.com/74/114874-050-6E04C88C/North-Face-Mount-Everest-Tibet-Autonomous-Region.jpg", alt="Local image")

text("### Year Select")
all_time = checkbox("Show All Time Data", value=True)
if not all_time:
    selected_year = slider("Select a Year", min_val=min_year, max_val=max_year, step=1, default=2024)
else:
    selected_year = None
    
# -- Data Filtering --
if all_time:
    display_df = filtered_df.copy()
    display_text = "All Time"
else:
    if selected_year in valid_years:
        display_df = filtered_df[filtered_df['year'] == selected_year]
        display_text = str(selected_year)
    else:
        display_df = pd.DataFrame(columns=filtered_df.columns)
        display_text = str(selected_year)

# -- Total Expeditions Count --
total_exped = len(display_df)
text(f"### Total Expeditions: **{total_exped:,}** ({display_text})")

# -- Conditional Visuals --
if total_exped == 0:
    text("⚠️ No expeditions found for the selected view.")
else:
    # SECTION 1: Most Climbed Peaks
    top_peaks = (
        display_df.groupby(['nation', 'peakid'])
        .size().reset_index(name='count')
        .merge(peaks_df[['peakid', 'pkname']], on='peakid', how='left')
        .dropna(subset=['pkname'])
    )
    top_peaks = top_peaks.sort_values('count', ascending=False).groupby('nation').head(5)

    fig_peaks = px.bar(top_peaks, x='pkname', y='count', color='nation',
                       title=f"Top Peaks Climbed by Nation ({display_text})",
                       labels={'pkname': 'Peak Name', 'count': 'Expeditions'},
                       barmode='group')
    fig_peaks.update_layout(xaxis_tickangle=-45)
    plotly(fig_peaks)

    # SECTION 2: Summit Success Rate
    display_df['was_successful'] = display_df['smtmembers'].fillna(0) > 0
    success_rate_df = (
        display_df.groupby('nation')['was_successful']
        .mean().reset_index(name='success_rate')
        .sort_values('success_rate', ascending=True)
    )

    fig_success = px.bar(success_rate_df, x='success_rate', y='nation',
                         orientation='h',
                         title=f"Summit Success Rate by Nation ({display_text})",
                         labels={'success_rate': 'Success Rate', 'nation': 'Country'},
                         text=success_rate_df['success_rate'].apply(lambda x: f"{x:.1%}"))
    fig_success.update_traces(textposition='outside')
    plotly(fig_success)

    # SECTION 3: Expeditions Over Time (only for All Time)
    if all_time:
        year_df = (
            filtered_df.groupby(['year', 'nation'])
            .size().reset_index(name='count')
        )
        fig_year = px.line(year_df, x='year', y='count', color='nation',
                           title="Expeditions Over Time by Nation",
                           labels={'count': 'Expeditions'})
        plotly(fig_year)

    # SECTION 4: World Map (always shown if data exists)
    map_data = (
        display_df['nation'].value_counts()
        .reset_index(name='expeditions')
        .rename(columns={'index': 'nation'})
    )

    fig_map = px.choropleth(
        map_data,
        locations='nation',
        locationmode='country names',
        color='expeditions',
        title=f"🌐 Expeditions by Country ({display_text})",
        color_continuous_scale='Blues',
        labels={'expeditions': 'Number of Expeditions'}
    )
    fig_map.update_geos(showframe=False, showcoastlines=True, projection_type="equirectangular")
    plotly(fig_map)
