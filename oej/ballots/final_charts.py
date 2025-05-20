from oej.ballots.counters import generate_ranges
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np


def create_probability_bar_chart(show_vertical=True):
    """
    Crea una gráfica de barras horizontal que muestra los rangos de probabilidad
    con textura para las personas electas y barras verticales adicionales en
    ubicaciones específicas.
    """

    # Datos para las barras verticales adicionales
    vertical_data = {
        "below_right": [
            { "label": "Una persona candidata de un sexo y al menos dos del otro sexo, compitiendo por una vacante",
              "value": 68 },
            { "label": "Misma cantidad de vacantes y personas candidatas", "value": 9 },
            { "label": "Misma cantidad de vacantes para un sexo y personas de ese mismo sexo", "value": 46 },
            { "label": "Aumenta a 100% de probabilidad por ajuste para garantizar equidad de género", "value": 10 },
        ],
        "above_left": [
            { "label": "Con probabilidad --> Reglas de paridad", "value": 26 },
            { "label": "Una persona candidata de un sexo y al menos dos del otro sexo, compitiendo por una vacante",
              "value": 175 },
        ],
        "below_left": [
            {
                "label": "Muchas persona candidatas (3 o más) de un sexo y pocas del otro sexo (2 o 3) compitiendo por una vacante",
                "value": 107 },
            {
                "label": "Una persona candidata de un sexo y al menos dos del otro sexo, compitiendo por una vacante; pero con posibilidades mínimas de asignación por equidad de género",
                "value": 14 },
        ]
    }

    # Obtener los datos
    ranges_data = generate_ranges(show_prints=False)

    # Dimensiones de la figura
    total_width_px = 1000
    total_height_px = 1000  # 80px altura de barra + 400px de espacio en blanco

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
    ax.set_facecolor('none')

    # Calcular población total para escalar
    total_population = sum(data["suma"] for data in ranges_data)

    # Configurar mapa de colores - probemos con 'turbo' que es más contrastante
    # cmap = plt.colormaps['turbo'].resampled(len(ranges_data))
    # cmap = plt.colormaps['cividis'].resampled(len(ranges_data))
    # cmap = plt.colormaps['cool_r'].resampled(len(ranges_data))
    cmap = plt.colormaps['cool_r'].resampled(16)

    # Inicializar posición x
    x_position = margin_left_px

    # Diccionario para almacenar información sobre barras con "add"
    add_bars_info = {}
    max_secondary_value = 0
    bar_secondary_width = 40

    # Dibujar barras para cada rango
    for idx, data in enumerate(ranges_data):
        # Calcular ancho proporcional a la población
        if total_population > 0:
            width = (data["suma"] / total_population) * available_width
        else:
            width = 0

        if width > 0:  # Solo dibuja si hay datos
            # Dibujar la barra principal
            color_idx = data["idx"]  # Usar el índice proporcionado por los datos
            rect = plt.Rectangle(
                (x_position, margin_bottom_px),
                width,
                bar_height_px,
                color=cmap(color_idx),
                ec='white',
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
                    edgecolor='#00000080',
                    linewidth=1
                )
                ax.add_patch(hatched_rect)

            # Si esta barra tiene un "add", guardar información para las barras verticales
            if "add" in data:
                # if data["add"] == "above_right":
                #     x_pos_vertical = x_position + width - bar_height_px
                # elif data["add"] == "below_left":
                #     x_pos_vertical = x_position
                # else:
                #     x_pos_vertical = (total_width_px - x_position) / 2
                if data["add"] == "above_left":
                    x_pos_vertical = margin_left_px
                elif data["add"] == "below_left":
                    x_pos_vertical = x_position
                else:
                    x_pos_vertical = x_position + width - bar_secondary_width
                add_bars_info[data["add"]] = {
                    "x_pos_vertical": x_pos_vertical,
                    "width": width,
                    "suma": data["suma"],
                    "color": cmap(color_idx)
                }
                max_secondary_value = max(max_secondary_value, data["suma"])

            # Mover posición x para la siguiente barra
            x_position += width + gap_between_bars

    # Agregar barras verticales adicionales
    # Parámetros para barras verticales
    vertical_bar_gap = 1  # Línea blanca entre barras verticales

    # Parámetros específicos para cada ubicación
    vertical_bars_params = {
        "above_left": {
            "y_position": margin_bottom_px + bar_height_px + 65,  # 10px debajo de la barra horizontal
            "direction": 1,  # Hacia arriba
        },
        "below_left": {
            "y_position": margin_bottom_px - 35,  # 10px encima de la barra horizontal
            "direction": -1,  # Hacia arriba
        },
        "below_right": {
            "y_position": margin_bottom_px - 35,  # 10px debajo de la barra horizontal
            "direction": -1,  # Hacia abajo
        }
    }

    # Dibujar barras verticales para cada ubicación
    max_height_vertical_bar = 280
    if show_vertical:
        for add_location, params in vertical_bars_params.items():
            if add_location in add_bars_info and add_location in vertical_data:
                bar_info = add_bars_info[add_location]
                data_values = vertical_data[add_location]
                bar_height = (max_height_vertical_bar *
                              (bar_info["suma"] / max_secondary_value))

                # Calcular ancho total disponible para este grupo
                # available_vertical_width = bar_info["width"]

                # Inicializar posición y dentro de la sección
                local_y_position = params["y_position"]

                # Encontrar el total de valores en este grupo para normalización
                total_group_value = sum(item["value"] for item in data_values)

                # Calcular ancho para cada barra incluyendo el espacio entre ellas
                # bar_width = (available_vertical_width - (len(data_values) - 1)
                #              * vertical_bar_gap) / len(data_values)
                # bar_width = bar_info["width"]  # Ancho fijo para cada barra

                # Dibujar cada barra vertical
                for item in data_values:
                    normalized_height = ((item["value"] / total_group_value)
                                         * bar_height)

                    # Dibujar barra vertical
                    if params["direction"] == 1:  # Hacia arriba
                        rect = plt.Rectangle(
                            (bar_info["x_pos_vertical"], local_y_position),
                            bar_secondary_width,
                            normalized_height,
                            color=bar_info["color"],
                            ec='white',
                            linewidth=0.5
                        )
                        local_y_position += normalized_height + vertical_bar_gap
                    else:  # Hacia abajo
                        rect = plt.Rectangle(
                            (bar_info["x_pos_vertical"],
                             local_y_position - normalized_height),
                            bar_secondary_width,
                            normalized_height,
                            color=bar_info["color"],
                            ec='white',
                            linewidth=0.5
                        )
                        local_y_position -= normalized_height + vertical_bar_gap

                    ax.add_patch(rect)

                    # Mover posición x para la siguiente barra
                    # local_x_position += bar_width + vertical_bar_gap


    # Establecer límites del eje
    ax.set_xlim(0, total_width_px)
    ax.set_ylim(0, total_height_px)

    # Eliminar ejes y etiquetas
    ax.set_axis_off()

    return fig


# Para usar la función:
def main():
    fig = create_probability_bar_chart()
    fig.show()
    ## save in fixture/charts/probability_bar_chart.png
    fig.savefig("fixture/charts/probability_bar_chart.png", dpi=300, bbox_inches='tight')

