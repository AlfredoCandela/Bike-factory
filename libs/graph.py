import matplotlib.pyplot as plt
import seaborn as sns


def plot_gantt(process_log, final_process, sim_time):
    sns.set_theme(style='ticks', context='talk')

    unique_processes = list(set(item['process_id'] for item in process_log))
    palette = sns.color_palette('Set3', n_colors=len(unique_processes))
    color_dict = {process: palette[i] for i, process in enumerate(unique_processes)}

    fig, ax = plt.subplots(figsize=(12, 6))
    for item in process_log:
        process = item['process_id']
        start = item['start']
        finish = item['end']
        duration = finish - start
        #ax.axvline(x=start, color='gray', linewidth=0.8, alpha=0.5)
        #ax.axvline(x=finish, color='gray', linewidth=0.8, alpha=0.5)
        ax.barh(y=process, width=duration, left=start,
                color=color_dict[process], edgecolor='black')

    ax.set_xlabel('Time (minutes)')
    bikes_hour = final_process.out_container.level*60/sim_time
    ax.set_title(f'Gantt Chart\nProductivity: {bikes_hour:.2f} bikes/hour')
    ax.grid(axis='x')
    plt.tight_layout()

def plot_occupancy_rate(process_log, sim_time):
    sns.set_theme(style='ticks', context='talk')
    unique_processes = list(set(item['process_id'] for item in process_log))
    palette = sns.color_palette('Set3', n_colors=len(unique_processes))
    color_dict = {process: palette[i] for i, process in enumerate(unique_processes)}

    durations = {}
    for unique_process in unique_processes:
        durations[unique_process] = 0
    
    for item in process_log:
        durations[item['process_id']] += item["end"] - item["start"]

    fig, ax = plt.subplots(figsize=(12, 6))
    for process in durations:
        if process == 'Request shipment': continue
        relative_duration =  durations[process] *100/sim_time
        ax.bar(x=process.replace(' ','\n'), height=relative_duration, color=color_dict[process], edgecolor='black')
        ax.set_ylabel('Active time (%)')

    ax.set_title('Occupancy rate')
    ax.grid(axis='y')
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=12)
    ax.set_ylim((0,100))
    plt.tight_layout()

def plot_inventory_graph(stock_log):
    max_curves = 10
    
    plt.figure(figsize=(12, 8))
    count = 0
    for item in stock_log:
        if count >= max_curves: break
        if item == 'time': continue
        plt.plot(stock_log['time'], stock_log[item], label=item.replace('_',' '))
        count += 1

    plt.title("Inventory levels")
    plt.xlabel("Time (min)")
    plt.ylabel("Quantity")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
