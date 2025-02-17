import matplotlib
matplotlib.use('TkAgg')  # 或者 'Agg', 'Qt5Agg', 'Qt4Agg', 'GTK3Agg', 等等

import matplotlib.pyplot as plt
import seaborn as sns

# passed_values = []
# total_used_values = []
# this_used_values = []
# enter_hour_nums = {}
# exit_hour_nums = {}
# enter_nums = []
# exit_nums = []
hours = list(range(1, 24))

# 假设你的数据文件名为 'data.txt'
filename = "statistics.log"

# 读取文件并解析数据
with open(filename, "r") as file:
    lines = file.readlines()
    this_used_values = eval(lines[3])
    # 注意,这里需要用float,不能用int,因为有很多值比较小,容易引起舍入问题
    this_used_values = [int(x) / 50 for x in this_used_values]
    total_used_values = eval(lines[4])
    total_used_values = [int(x) / 60 / 15 for x in total_used_values]
    passed_values = eval(lines[5])
    passed_values = [int(x) for x in passed_values]
    enter_hour_nums = eval(lines[6])
    exit_hour_nums = eval(lines[7])

enter_nums = [int(enter_hour_nums[x]) for x in hours]
exit_nums = [int(exit_hour_nums[x]) for x in hours]
# 使用 seaborn 设置图形样式
sns.set_theme(style="whitegrid")

# 创建图形
plt.figure(figsize=(12, 6))

# 创建 passed 的区间概率图（直方图）
plt.subplot(3, 2, 1)
sns.histplot(passed_values, color="blue", stat="probability", binwidth=1)
plt.title("Distribution of Passed Values")
plt.xlabel("Passed Value")
plt.ylabel("probability")

# 创建 used 的区间概率图（直方图）
plt.subplot(3, 2, 2)
sns.histplot(total_used_values, color="green", stat="probability", binwidth=1)
plt.title("Distribution of Used Time (15 min)")
plt.xlabel("total Used Time")
plt.ylabel("probability")

plt.subplot(3, 2, 3)
sns.histplot(this_used_values, color="brown", stat="probability", binwidth=1)
plt.title("Distribution of Used Time (50 s)")
plt.xlabel("this Used Time")
plt.ylabel("probability")

plt.subplot(3, 2, 4)
sns.lineplot(x=hours, y=enter_nums, color="green")
plt.title("enter")
plt.xlabel("hour")
plt.ylabel("num")

plt.subplot(3, 2, 4)
sns.lineplot(x=hours, y=exit_nums, color="red")
plt.title("exit")
plt.xlabel("hour")
plt.ylabel("num")

# 显示图形
plt.tight_layout()
plt.show()
