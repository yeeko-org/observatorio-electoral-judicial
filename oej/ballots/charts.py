import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np


def show_chart():
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np

    # Create DataFrame from the provided data
    data = {
        'materia': [
            'MIXTO', 'PENAL', 'ADMINISTRATIVA', 'CIVIL', 'LABORAL',
            'TRABAJO', "1", "2", "3", "4", "5"],
        'mujeres': [345, 242, 193, 130, 130, 96, 30, 22, 34, 26, 27],
        'hombres': [579, 347, 227, 159, 142, 137, 39, 54, 43, 27, 28]
    }
    df = pd.DataFrame(data)

    # Calculate totals and percentages
    df['total'] = df['mujeres'] + df['hombres']
    df['pct_mujeres'] = df['mujeres'] / df['total'] * 100
    df['pct_hombres'] = df['hombres'] / df['total'] * 100

    # Sort by total (largest first)
    df = df.sort_values('total', ascending=True)

    # Calculate the grand total and overall percentages
    total_mujeres = df['mujeres'].sum()
    total_hombres = df['hombres'].sum()
    total_general = total_mujeres + total_hombres
    pct_total_mujeres = total_mujeres / total_general * 100

    # Colors
    color_mujeres = '#4CAF50'  # Green
    color_hombres = '#FF9800'  # Orange

    # Create figure and axis
    fig, ax = plt.subplots(num=2, figsize=(12, 10))
    # plt.subplots_adjust(top=0.85)

    # move ax to below the title
    ax.set_position([0.2, 0.2, 0, 0.8])


    # Initialize y-coordinate
    y = 0
    # Plot each category
    for _, row in df.iterrows():
        # Calculate dimensions
        height = row['total'] / total_general
        width_mujeres = row['pct_mujeres'] / 100
        width_hombres = row['pct_hombres'] / 100

        # Plot rectangles
        ax.add_patch(
            plt.Rectangle(
                (0, y), width_mujeres, height,
                facecolor=color_mujeres, edgecolor='white', linewidth=1)
        )
        ax.add_patch(
            plt.Rectangle(
                (width_mujeres, y), width_hombres, height,
                facecolor=color_hombres, edgecolor='white', linewidth=1)
        )

        # Add percentage labels
        ax.text(width_mujeres / 2, y + height / 2,
                f"{row['pct_mujeres']:.0f}%", size=11,
                ha='center', va='center', color='white', fontweight='bold')
        ax.text(
            width_mujeres + width_hombres / 2, y + height / 2,
            f"{row['pct_hombres']:.0f}%", size=11,
            ha='center', va='center', color='white', fontweight='bold')

        # Add category label
        ax.text(1.02, y + height / 2, f"{row['materia']} ({row['total']:,})",
                va='center', fontweight='bold', size=11)

        # Update y for next bar
        y += height

    # Set plot limits
    ax.set_xlim(0, 1.3)
    ax.set_ylim(0, 1)

    # Remove axes
    ax.axis('off')

    # Add vertical dotted line at 50%
    ax.axvline(0.5, ymin=0, ymax=1, linestyle='--', color='gray')

    # Add title and headers
    plt.title(
        "Personas Candidatas por sexo", fontsize=16, fontweight='bold',
        loc='left', pad=20)
    # fig.text(0.25, 0.95, 'Mujeres', fontsize=14, color=color_mujeres, ha='center')
    fig.text(0.015, 0.95, 'Mujeres', fontsize=14, color=color_mujeres, ha='left')
    fig.text(0.75, 0.95, 'Hombres', fontsize=14, color=color_hombres, ha='right')

    # Add 50% marker
    plt.text(0.5, 1, '50%', fontsize=12, ha='center')
    # plt.arrow(
    #     0.5, 1, 0, -0.01, head_width=0.02, head_length=0.01, fc='black', ec='black')

    # Add total percentages
    fig.text(
        0.015, 0.9, f"{pct_total_mujeres:.1f}%", fontsize=16, color=color_mujeres,
        ha='left', fontweight='bold')

    # Add total label
    fig.text(0.88, 0.9, f"Total\n{total_general:,}", fontsize=12, ha='center')

    # Show plot
    plt.tight_layout()
    plt.show()


# show_chart()




def show_chart_by_range():
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np

    # Create DataFrame from the provided data
    data = {
        'materia': [
            "derrota asegurada", "+ de 6 competidores",
            "≈6 competidores por vacante", "≈5 competidores por vacante",
            "≈4 competidores por vacante", "≈3 competidores por vacante",
            "≈2 competidores por vacante",  "grandes posibilidades",
            "victoria asegurada"],
        'total': [298, 515, 355, 474, 570, 529, 254, 75, 132],
        'selected': [0, 58, 59, 93, 144, 184, 127, 51, 132]
    }
    df = pd.DataFrame(data)

    # Calculate totals and percentages
    # df['total'] = df['mujeres'] + df['selected']
    # df['pct_mujeres'] = df['mujeres'] / df['total'] * 100
    df['pct_selected'] = df['selected'] / df['total'] * 100


    # Calculate the grand total and overall percentages
    # total_mujeres = df['mujeres'].sum()
    total_selected = df['selected'].sum()
    total_general = df['total'].sum()
    pct_total_selected = total_selected / total_general * 100

    # Colors
    color_mujeres = '#4CAF5020'  # Green
    color_selected = '#FF9800'  # Orange

    # Create figure and axis
    fig, ax = plt.subplots(num=2, figsize=(12, 10))
    # plt.subplots_adjust(top=0.85)

    # move ax to below the title
    ax.set_position([0.2, 0.2, 0, 0.8])


    # Initialize y-coordinate
    y = 0
    # Plot each category
    for _, row in df.iterrows():
        # Calculate dimensions
        height = row['total'] / total_general
        # width_mujeres = row['pct_mujeres'] / 100
        selected = row['selected']
        width_selected = row['pct_selected'] / 100

        # Plot rectangles
        ax.add_patch(
            plt.Rectangle(
                (0, y), 1, height,
                facecolor=color_selected, edgecolor='white', linewidth=1)
        )

        ax.add_patch(
            plt.Rectangle(
                (0, y), width_selected, height,
                facecolor=color_selected,
                hatch='//', alpha=1,
                edgecolor='white', linewidth=1)
        )

        ax.text(width_selected + 0.01, y + height / 2,
                f"{selected} victorias", size=11,
                ha='left', va='center', color='white', fontweight='bold')

        # Add category label
        ax.text(1.02, y + height / 2, f"{row['materia']} ({row['total']:,})",
                va='center', fontweight='bold', size=11)

        # Update y for next bar
        y += height

    # Set plot limits
    ax.set_xlim(0, 1.4)
    ax.set_ylim(0, 1)

    # Remove axes
    ax.axis('off')

    # Add vertical dotted line at 50%
    ax.axvline(0.5, ymin=0, ymax=1, linestyle='--', color='gray')

    # Add title and headers
    plt.title(
        "Personas Candidatas por sexo", fontsize=16, fontweight='bold',
        loc='left', pad=20)
    # fig.text(0.25, 0.95, 'Mujeres', fontsize=14, color=color_mujeres, ha='center')
    fig.text(0.015, 0.95, 'Mujeres', fontsize=14, color=color_mujeres, ha='left')
    fig.text(0.75, 0.95, 'Hombres', fontsize=14, color=color_selected, ha='right')

    # Add 50% marker
    plt.text(0.5, 1, '50%', fontsize=12, ha='center')
    # plt.arrow(
    #     0.5, 1, 0, -0.01, head_width=0.02, head_length=0.01, fc='black', ec='black')

    # Add total percentages
    # fig.text(
    #     0.015, 0.9, f"{pct_total_mujeres:.1f}%", fontsize=16, color=color_mujeres,
    #     ha='left', fontweight='bold')
    fig.text(
        0.75, 0.9, f"{pct_total_selected:.1f}%", fontsize=16, color=color_selected,
        ha='right', fontweight='bold')

    # Add total label
    fig.text(0.88, 0.9, f"Total\n{total_general:,}", fontsize=12, ha='center')

    # Show plot
    plt.tight_layout()
    plt.show()



# show_chart_by_range()


