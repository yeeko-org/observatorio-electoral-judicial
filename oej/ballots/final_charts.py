import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np


def create_probability_bar_chart():
    """
    Crea una gráfica de barras horizontal que muestra los rangos de probabilidad
    con textura para las personas electas.
    """
    from oej.ballots.counters import generate_ranges

    # Obtener los datos
    ranges_data = generate_ranges(show_prints=False)

    # Dimensiones de la figura
    total_width_px = 1000
    total_height_px = 880  # 40px altura de barra + 400px de espacio en blanco

    # Parámetros de la barra
    margin_left_px = 20
    margin_right_px = 20
    margin_bottom_px = 400
    bar_height_px = 80
    gap_between_bars = 1  # Pequeño espacio entre barras para distinguirlas

    # Calcular ancho disponible para las barras
    available_width = total_width_px - margin_left_px - margin_right_px - gap_between_bars * (len(ranges_data) - 1)

    # Crear figura con dimensiones exactas en píxeles
    dpi = 50  # puntos por pulgada
    fig = plt.figure(figsize=(total_width_px / dpi, total_height_px / dpi), dpi=dpi)

    # Crear eje que cubra toda la figura
    ax = fig.add_axes([0, 0, 1, 1])

    # Establecer fondo blanco
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # Calcular población total para escalar
    total_population = sum(data["suma"] for data in ranges_data)

    # Configurar mapa de colores - probemos con 'turbo' que es más contrastante
    # cmap = plt.colormaps['turbo'].resampled(len(ranges_data))
    # cmap = plt.colormaps['cividis'].resampled(len(ranges_data))
    # cmap = plt.colormaps['cool_r'].resampled(len(ranges_data))
    cmap = plt.colormaps['cool_r'].resampled(16)

    # Inicializar posición x
    x_position = margin_left_px

    # Dibujar barras para cada rango
    for idx, data in enumerate(ranges_data):
        # Calcular ancho proporcional a la población
        if total_population > 0:
            width = (data["suma"] / total_population) * available_width
        else:
            width = 0

        if width > 0:  # Solo dibuja si hay datos
            # Dibujar la barra principal
            rect = plt.Rectangle(
                (x_position, margin_bottom_px),
                width,
                bar_height_px,
                # color=cmap(idx),
                color=cmap(data["pos_color"]),
                ec='white',  # Borde negro para mejor visibilidad
                linewidth=0.5
            )
            ax.add_patch(rect)

            # Añadir patrón rayado para personas electas
            if data["personas_electas"] > 0:
                print("electas", data["personas_electas"])
                elected_proportion = float(data["personas_electas"] / 100)
                print("elected_proportion", elected_proportion)
                hatched_height = bar_height_px * (elected_proportion / data["suma"])

                hatched_rect = plt.Rectangle(
                    (x_position, margin_bottom_px),
                    width,
                    hatched_height,
                    hatch='//',
                    fill=False,
                    edgecolor='#00000080',  # Color del borde
                    linewidth=1
                )
                ax.add_patch(hatched_rect)

            # Mover posición x para la siguiente barra
            x_position += width + gap_between_bars

    # Establecer límites del eje
    ax.set_xlim(0, total_width_px)
    ax.set_ylim(0, total_height_px)

    # Eliminar ejes y etiquetas
    ax.set_axis_off()

    return fig


# Para usar la función:
def main():
    fig = create_probability_bar_chart()
    plt.show()

