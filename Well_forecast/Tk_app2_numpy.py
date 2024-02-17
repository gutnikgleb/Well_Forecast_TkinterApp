import sys
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import os
import numpy as np
from datetime import datetime
from matplotlib.dates import YearLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from dateutil.relativedelta import relativedelta
from csv import writer

root = tk.Tk()
root.title("Well forecast")
root.resizable(False, False)


def on_closing():
    plt.close()
    root.destroy()
    sys.exit()


root.protocol("WM_DELETE_WINDOW", on_closing)

current_graph = '2 x 2'
today = datetime.now()
fields = {'Мега': {'АВ1(3)': 0.858, 'БВ8': 0.847, 'ЮВ1(1)': 0.828},
          "Вата": {'АВ1(3)': 0.895, 'БВ8': 0.85, 'БВ19-22': 0.831, 'ЮВ1(1)': 0.834},
          "Аган": {'АВ1(3)': 0.872, 'БВ8-9': 0.838, 'БВ17-21': 0.837, 'ЮВ1(1)': 0.822},
          "Ю-Аган": {'ЮВ1(1)': 0.826}}
dates = []
steps_25years = np.arange(0, 12 * 25)
steps_25years = np.insert(steps_25years, 0, 0)
fluid = np.zeros(12 * 25 + 1, dtype='float64')
water_cut = np.zeros(12 * 25 + 1, dtype='float64')
oil = np.zeros(12 * 25 + 1, dtype='float64')
cum_oil = np.zeros(12 * 25 + 1, dtype='float64')


def calculate_params(current_date: datetime = today,
                     field: str = 'Мега', reservoir: str = 'ЮВ1(1)',
                     ql_0: float = 100, wc_0: float = 50,
                     d_q: float = 0.3, d_wc: float = 0.3,
                     s_ql: float = 0.5, s_wc: float = 0.95):
    global fluid, water_cut, oil, cum_oil

    update_dates_list(month=str(current_date.month), year=str(current_date.year))
    ro = fields[field][reservoir]
    fluid[1:] = np.round((ql_0 - s_ql * ql_0) * np.exp(-d_q * steps_25years[1:]) + s_ql * ql_0, 2)
    water_cut[1:] = np.round((wc_0 - s_wc * 100) * np.exp(-d_wc * steps_25years[1:]) + s_wc * 100, 2)
    oil[1:] = np.round(fluid[1:] * (100 - water_cut[1:]) / 100 * ro, 2)
    cum_oil = np.round(np.cumsum(oil * 30 / 1000), 2)


def update_dates_list(month: str, year: str):
    global dates

    month = month if len(month) == 2 else '0' + month
    first_date = np.datetime64(f"{year}-{month}")
    last_date = first_date + (12 * 25 + 1)
    dates = np.arange(first_date, last_date)


fig = plt.figure(figsize=(8, 5))
ax1 = fig.add_axes((0.1, 0.14, 0.8, 0.82))
ax2 = ax1.twinx()
line_fluid = ax1.plot([], [])
line_oil = ax1.plot([], [])
line_cum_oil = ax2.plot([], [])
line_water_cut = ax2.plot([])


def graph_2x2():
    global fig, line_fluid, line_oil, line_cum_oil, line_water_cut, canvas

    # линии левой оси
    line_fluid = ax1.plot(dates, fluid, '-', label='Дебит жидкости, м3/сут', color=(16 / 255, 230 / 255, 41 / 255))
    line_oil = ax1.plot(dates, oil, '-', label='Дебит нефти, т/сут', color=(153 / 255, 102 / 255, 0 / 255))
    ax1.set_ylabel('Дебит нефти, т/сут\nДебит жидкости, м3/сут', fontsize=10)
    ax1_maxOY = fluid[1] * 1.1
    ax1.set_ylim(bottom=0, top=ax1_maxOY)
    ax1.set_xlim(left=(dates[0] - 5), right=dates[-1])
    ax1.xaxis.set_major_locator(YearLocator(base=2))
    ax1.grid(linestyle='--')

    # линии правой оси
    line_cum_oil = ax2.plot(dates, cum_oil, '--', label='Накопленная нефть, тыс.т',
                            color=(255 / 255, 204 / 255, 0 / 255))
    line_water_cut = ax2.plot(dates, water_cut, '-', label='Обводненность, %', color=(0 / 255, 0 / 255, 255 / 255))
    ax2.set_ylabel('Обводненность, %\nНакопленная нефть, тыс.т', fontsize=10)
    ax2_maxOY = cum_oil[-1] * 1.1 if water_cut[-1] < cum_oil[-1] else 100
    ax2.set_ylim(bottom=0, top=ax2_maxOY)

    # легенда
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines = lines1 + lines2
    labels = labels1 + labels2
    ax1.legend(lines, labels, loc='lower center', frameon=False, ncol=4, fontsize=8.3,
               bbox_to_anchor=(0.5, -0.17))

    canvas.draw()


def graph_3x1():
    global fig, line_fluid, line_oil, line_cum_oil, line_water_cut, canvas

    # линии левой оси
    line_fluid = ax1.plot(dates, fluid, '-', label='Дебит жидкости, м3/сут', color=(16 / 255, 230 / 255, 41 / 255))
    line_oil = ax1.plot(dates, oil, '-', label='Дебит нефти, т/сут', color=(153 / 255, 102 / 255, 0 / 255))
    line_water_cut = ax1.plot(dates, water_cut, '-', label='Обводненность, %', color=(0 / 255, 0 / 255, 255 / 255))
    ax1.set_ylabel('Дебит нефти, т/сут; Дебит жидкости, м3/сут\nОбводненность, %', fontsize=10)
    ax1_maxOY = fluid[1] * 1.1 if water_cut[-1] < fluid[1] else 100
    ax1.set_ylim(bottom=0, top=ax1_maxOY)
    ax1.set_xlim(left=(dates[0] - 5), right=dates[-1])
    ax1.xaxis.set_major_locator(YearLocator(base=2))
    ax1.grid(linestyle='--')

    # линии правой оси
    line_cum_oil = ax2.plot(dates, cum_oil, '--', label='Накопленная нефть, тыс.т',
                            color=(255 / 255, 204 / 255, 0 / 255))
    ax2.set_ylabel('Накопленная нефть, тыс.т', fontsize=10)
    ax2_maxOY = cum_oil[-1] * 1.1
    ax2.set_ylim(bottom=0, top=ax2_maxOY)

    # легенда
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines = lines1 + lines2
    labels = labels1 + labels2
    ax1.legend(lines, labels, loc='lower center', frameon=False, ncol=4, fontsize=8.3,
               bbox_to_anchor=(0.48, -0.17))

    canvas.draw()


def update_info(*args):
    calculate_params(current_date=datetime.strptime(start_date_var.get() + '.1', "%m.%Y.%d"),
                     field=field_var.get(), reservoir=reservoir_var.get(),
                     ql_0=float(Ql_input_entry.get()), wc_0=float(WC_input_entry.get()),
                     s_ql=Ql_scale.get() / 100, d_q=Ql_tp_value.get() / 2,
                     s_wc=WC_scale_value.get() / 100, d_wc=WC_tp_value.get() / 2)
    update_forecast_info()
    update_plot()


def update_plot(*args):
    line_fluid[0].set_data(dates, fluid)
    line_oil[0].set_data(dates, oil)
    line_cum_oil[0].set_data(dates, cum_oil)
    line_water_cut[0].set_data(dates, water_cut)
    if current_graph == '2 x 2':
        ax1_maxOY = fluid[1] * 1.1
        ax1.set_ylim(bottom=0, top=ax1_maxOY)
        ax2_maxOY = cum_oil[-1] * 1.1 if water_cut[-1] < cum_oil[-1] else 100
        ax2.set_ylim(bottom=0, top=ax2_maxOY)
    elif current_graph == '3 x 1':
        ax1_maxOY = fluid[1] * 1.1 if water_cut[-1] < fluid[1] else 100
        ax1.set_ylim(bottom=0, top=ax1_maxOY)
        ax2_maxOY = cum_oil[-1] * 1.1
        ax2.set_ylim(bottom=0, top=ax2_maxOY)
    ax1.set_xlim(left=(dates[0] - 5), right=dates[-1])

    canvas.draw()


def update_forecast_info():
    Qoil_0_var.set(f"{oil[1]} т/сут")
    Qoil_1_var.set(f"{oil[13]} т/сут")
    Qoil_2_var.set(f"{oil[25]} т/сут")
    Qoil_5_var.set(f"{oil[61]} т/сут")
    Qoil_25_var.set(f"{oil[-1]} т/сут")
    decline_rate_03_var.set(f"{round((fluid[1] - fluid[4]) / fluid[1] * 100)}%")
    decline_rate_1_var.set(f"{round((fluid[1] - fluid[13]) / fluid[1] * 100)}%")
    decline_rate_2_var.set(f"{round((fluid[1] - fluid[25]) / fluid[1] * 100)}%")
    decline_rate_25_var.set(f"{round((fluid[1] - fluid[-1]) / fluid[1] * 100)}%")
    cum_oil_1_var.set(f"{cum_oil[13]} тыс.т")
    cum_oil_5_var.set(f"{cum_oil[61]} тыс.т")
    cum_oil_25_var.set(f"{cum_oil[-1]} тыс.т")


def get_reservoir_names(event):
    field = field_var.get()
    new_values = [k for k in fields[field].keys()]
    combobox_reservoir['values'] = new_values
    reservoir_var.set(new_values[0])
    update_info()


def change_graph():
    input_date = start_date_var.get().split('.')
    input_date_datetime64 = np.datetime64(f"{input_date[1]}-{input_date[0]}")
    need_update = False

    if input_date_datetime64 != dates[1]:
        month = input_date[0]
        year = input_date[1]
        update_dates_list(month, year)
        need_update = True
    if graph_var.get() != current_graph:
        switch_graphs()
        need_update = False

    if need_update:
        update_plot()


def switch_graphs():
    global current_graph

    for artist in ax1.lines:
        artist.remove()
    for artist in ax2.lines:
        artist.remove()

    if current_graph == '2 x 2':
        graph_3x1()
        current_graph = '3 x 1'
    else:
        graph_2x2()
        current_graph = '2 x 2'


def save_results():
    current_directory = os.getcwd()
    results_directory = os.path.join(current_directory, 'results')
    if not os.path.exists(results_directory):
        os.makedirs(results_directory)

    well_name = well_name_var.get()
    fig.savefig(os.path.join(results_directory, f"plot_{well_name}.png"))

    with open(os.path.join(results_directory, f"parameters_{well_name}.csv"),
              mode='w', newline='') as file:
        wrtr = writer(file, delimiter=';')
        wrtr.writerow(['Date', 'Q_liq, m3/day', 'Q_oil, t/day', 'WC, %', 'Cum. oil, t*10^3'])
        date_strings = np.datetime_as_string(dates, unit='D')
        for i in range(len(dates)):
            wrtr.writerow([date_strings[i],
                           str(fluid[i]).replace('.', ','),
                           str(oil[i]).replace('.', ','),
                           str(water_cut[i]).replace('.', ','),
                           str(cum_oil[i]).replace('.', ',')])


# СЕКЦИЯ С ГРАФИКОМ
frame_plot = ttk.Frame(root)
frame_plot.grid(row=0, column=0, columnspan=6, rowspan=12)

canvas = FigureCanvasTkAgg(fig, master=frame_plot)
canvas_widget = canvas.get_tk_widget()
canvas_widget.grid(row=0, column=0, columnspan=6, rowspan=12)

# СЕКЦИЯ ВЫБОРА МЕСТОРОЖДЕНИЯ И ПЛАСТА И СКВАЖИНЫ
field_var = tk.StringVar(value='Мега')
combobox_feild = ttk.Combobox(values=[k for k in fields.keys()], textvariable=field_var, width=14, justify=tk.CENTER)
combobox_feild.grid(row=0, column=7, sticky='e')
combobox_feild.bind('<<ComboboxSelected>>', get_reservoir_names)

reservoir_var = tk.StringVar(value='АВ1(3)')
combobox_reservoir = ttk.Combobox(values=[k for k in fields['Мега'].keys()], textvariable=reservoir_var, width=14,
                                  justify=tk.CENTER)
combobox_reservoir.grid(row=0, column=8, sticky='w')
combobox_reservoir.bind('<<ComboboxSelected>>', update_info)

tk.Label(root, text="Имя скважины: ").grid(row=1, column=7)
well_name_var = tk.StringVar(value='KP-HW')
well_input = ttk.Entry(root, width=16, textvariable=well_name_var)
well_input.grid(row=1, column=8)

# СЕКЦИЯ ДЕБИТ ЖИДКОСТИ
tk.Label(root, text="Дебит жидкости: ").grid(row=2, column=7)
# Поле ввода для Qж
Ql_entry = tk.DoubleVar(value=None)
Ql_input_entry = ttk.Entry(root, width=16, textvariable=Ql_entry)
Ql_input_entry.insert(0, 10)
Ql_input_entry.grid(row=2, column=8)
Ql_entry.trace_add('write', update_info)
# Ползунок для стабилизированного участка
tk.Label(root, text="Коэффициент 1 ").grid(row=3, column=7)
Ql_scale_value = tk.IntVar(value=50)
Ql_scale = tk.Scale(root, orient='horizontal', from_=0, to=100, variable=Ql_scale_value, command=update_info)
Ql_scale.grid(row=3, column=8)
# Ползунок для темпа падения
tk.Label(root, text="Коэффициент 2 ").grid(row=4, column=7)
Ql_tp_value = tk.DoubleVar(value=0.5)
Ql_tp_scale = tk.Scale(root, orient='horizontal', from_=0, to=1, resolution=0.01, variable=Ql_tp_value,
                       command=update_info)
Ql_tp_scale.grid(row=4, column=8)

# СЕКЦИЯ ОБВОДНЕННОСТЬ
tk.Label(root, text="Обводненность: ").grid(row=5, column=7)
# Поле ввода для WC
WC_entry = tk.DoubleVar(value=None)
WC_input_entry = ttk.Entry(root, width=16, textvariable=WC_entry)
WC_input_entry.insert(0, 5)
WC_input_entry.grid(row=5, column=8)
WC_entry.trace_add('write', update_info)
# Ползунок для стабилизированного участка
tk.Label(root, text="Коэффициент 1 ").grid(row=6, column=7)
WC_scale_value = tk.IntVar(value=95)
WC_scale = tk.Scale(root, orient='horizontal', from_=0, to=100, variable=WC_scale_value, command=update_info)
WC_scale.grid(row=6, column=8)
# Ползунок для темпа набора
tk.Label(root, text="Коэффициент 2 ").grid(row=7, column=7)
WC_tp_value = tk.DoubleVar(value=0.5)
WC_tp_scale = tk.Scale(root, orient='horizontal', from_=0, to=1, resolution=0.01, variable=WC_tp_value,
                       command=update_info)
WC_tp_scale.grid(row=7, column=8)

# СЕКЦИЯ ИЗМЕНЕИЯ ГРАФИКА
tk.Label(root, text="Корректировка графика").grid(row=8, column=7, columnspan=2)
tk.Label(root, text="Дата ввода: ").grid(row=9, column=7)
start_date_var = tk.StringVar(value=(today + relativedelta(months=1)).strftime("%m.%Y"))
start_date_entry = ttk.Entry(root, width=16, textvariable=start_date_var)
start_date_entry.grid(row=9, column=8)
graph_var = tk.StringVar(value='2 x 2')
graph_chose_1 = ttk.Radiobutton(root, text='2 x 2', value='2 x 2', variable=graph_var)
graph_chose_1.grid(row=10, column=7)
graph_chose_2 = ttk.Radiobutton(root, text='3 x 1', value='3 x 1', variable=graph_var)
graph_chose_2.grid(row=10, column=8)
graph_btn = ttk.Button(root, text='Изменить график', command=change_graph)
graph_btn.grid(row=11, column=7, columnspan=2)

# СЕКЦИЯ СОХРАНЕНИЯ РЕЗУЛЬТАТОВ
save_btn = ttk.Button(root, text="Сохранить результаты", command=save_results)
save_btn.grid(row=18, column=7, columnspan=2)

# СЕКЦИЯ ОСНОВНЫХ ПОКАЗАТЕЛЕЙ РАСЧЕТА
# ДЕБИТ НЕФТИ
tk.Label(root, text="Дебит нефти").grid(row=13, column=0, columnspan=2)
tk.Label(root, text="Qн_0 = ").grid(row=14, column=0, sticky='e')
Qoil_0_var = tk.StringVar(value='--')
Qoil_0_label = tk.Label(root, textvariable=Qoil_0_var)
Qoil_0_label.grid(row=14, column=1, sticky='w')
tk.Label(root, text="Qн_1г = ").grid(row=15, column=0, sticky='e')
Qoil_1_var = tk.StringVar(value='--')
Qoil_1_label = tk.Label(root, textvariable=Qoil_1_var)
Qoil_1_label.grid(row=15, column=1, sticky='w')
tk.Label(root, text="Qн_2г = ").grid(row=16, column=0, sticky='e')
Qoil_2_var = tk.StringVar(value='--')
Qoil_2_label = tk.Label(root, textvariable=Qoil_2_var)
Qoil_2_label.grid(row=16, column=1, sticky='w')
tk.Label(root, text="Qн_5г = ").grid(row=17, column=0, sticky='e')
Qoil_5_var = tk.StringVar(value='--')
Qoil_5_label = tk.Label(root, textvariable=Qoil_5_var)
Qoil_5_label.grid(row=17, column=1, sticky='w')
tk.Label(root, text="Qн_25г = ").grid(row=18, column=0, sticky='e')
Qoil_25_var = tk.StringVar(value='--')
Qoil_25_label = tk.Label(root, textvariable=Qoil_25_var)
Qoil_25_label.grid(row=18, column=1, sticky='w')
tk.Label(root, text="").grid(row=19, column=0)  # пустая строка для красоты
# ТЕМП ПАДЕНИЯ
tk.Label(root, text="Темп падения Qж").grid(row=13, column=2, columnspan=2)
tk.Label(root, text="ТП_3мес = ").grid(row=14, column=2, sticky='e')
decline_rate_03_var = tk.StringVar(value='--%')
decline_rate_03_label = tk.Label(root, textvariable=decline_rate_03_var)
decline_rate_03_label.grid(row=14, column=3, sticky='w')
tk.Label(root, text="ТП_1г = ").grid(row=15, column=2, sticky='e')
decline_rate_1_var = tk.StringVar(value='--%')
decline_rate_1_label = tk.Label(root, textvariable=decline_rate_1_var)
decline_rate_1_label.grid(row=15, column=3, sticky='w')
tk.Label(root, text="ТП_2г = ").grid(row=16, column=2, sticky='e')
decline_rate_2_var = tk.StringVar(value='--%')
decline_rate_2_label = tk.Label(root, textvariable=decline_rate_2_var)
decline_rate_2_label.grid(row=16, column=3, sticky='w')
tk.Label(root, text="ТП_25г = ").grid(row=17, column=2, sticky='e')
decline_rate_25_var = tk.StringVar(value='--%')
decline_rate_25_label = tk.Label(root, textvariable=decline_rate_25_var)
decline_rate_25_label.grid(row=17, column=3, sticky='w')
# НАКОПЛЕННАЯ ДОБЫЧА
tk.Label(root, text="Накопленная добыча нефти").grid(row=13, column=4, columnspan=2)
tk.Label(root, text="НД_1г = ").grid(row=14, column=4, sticky='e')
cum_oil_1_var = tk.StringVar(value='--')
cum_oil_1_label = tk.Label(root, textvariable=cum_oil_1_var)
cum_oil_1_label.grid(row=14, column=5, sticky='w')
tk.Label(root, text="НД_5г = ").grid(row=15, column=4, sticky='e')
cum_oil_5_var = tk.StringVar(value='--')
cum_oil_5_label = tk.Label(root, textvariable=cum_oil_5_var)
cum_oil_5_label.grid(row=15, column=5, sticky='w')
tk.Label(root, text="НД_25г = ").grid(row=16, column=4, sticky='e')
cum_oil_25_var = tk.StringVar(value='--')
cum_oil_25_label = tk.Label(root, textvariable=cum_oil_25_var)
cum_oil_25_label.grid(row=16, column=5, sticky='w')

calculate_params()
update_forecast_info()
graph_2x2()
root.mainloop()
