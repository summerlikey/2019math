import datetime
import time

import numpy
import xlrd
import math

# 时间字符转转化为公秒时间sample
expire_time1 = "2017/12/18 13:42:13.000."
d1 = datetime.datetime.strptime(expire_time1, "%Y/%m/%d %H:%M:%S.%f.")
time_sec_float = time.mktime(d1.timetuple())
print("测试: ", time_sec_float)
print("程序有六处需要修改文件名")


# 文件最后一列为异常标记，倒数第二列为时间片区
# 预处理过程:
# 1.将数据按时间分片段,倒数第二列从0开始
# 2.按怠速180s将数据标记为怠速.将超过180s的片段删除
# 2.5.保留启动前速度20s，即速度小于10往前推20s
# 3.按加速度超过3.96m/s2和加速度小于-8m/s2标记为异常(注意加速度在时间片段的变化，二者速度不连续)最后一列
# 预处理过后,将数据按时间再次划分片段
#


# 按时间分区
def divided_time(my_list):
    flag = 0
    for I in range(len(my_list) - 1):
        my_list[I][14] = flag
        if (my_list[I + 1][0] - my_list[I][0]) > 1:
            flag = flag + 1
    my_list[-1][14] = flag
    return


# 数据保存二维源数据
def save_data(my_list):
    fo = open("data_01_solve.txt", "w")
    for I in range(len(my_list)):
        for j in range(len(my_list[I])):
            fo.write(str(my_list[I][j]) + " ")
        fo.write("\n")
    fo.close()
    return


# 运动学数据保存（三维）
def save_data_dynamic(my_list):
    fo3 = open("data_01_dynamic.txt", "w")
    for I in range(len(my_list)):
        for J in range(len(my_list[I])):
            for K in range(len(my_list[I][J])):
                fo3.write(str(my_list[I][J][K]) + " ")
            fo3.write("\n")
        fo3.write("\n")
    fo3.write("总数据量:"+str(total_num)+"\n")
    fo3.write("正常数据量:"+str(total_no_error)+"\n")
    fo3.write("运动学片段总数"+str(total_num_divided)+"\n")
    fo3.close()
    return


# 特征值保存
def save_special_value(my_list):
    fo4 = open("data_01_special.txt", "w")
    for i in range(len(my_list)):
        fo4.write("%d " % i)
        for j in range(len(my_list[i])):
            fo4.write(str(my_list[i][j])+" ")
        fo4.write("\n")
    return


# 数据预处理,0表示数据正常,大于0表示不正常,本函数进行异常标记
def data_pre_process(my_list):
    # 怠速累计，速度小于10的累积到180个后显示为无效阶段
    tol = 0
    for I in range(len(my_list)-1):
        if tol > 180 and my_list[I][1] < 10:
            my_list[I][15] = tol
        else:
            my_list[I][15] = 0
        if my_list[I][1] < 10:
            tol = tol + 1
        else:
            tol = 0
        # 加速度大于3.96m/s2或者加速度小于-8m/s2的为异常数据
        if my_list[I][-2] == my_list[I+1][-2]:
            acc = my_list[I+1][1] - my_list[I][1]
            # 单位换算
            acc = acc/3.6
            if acc > 3.96 or acc < -8:
                my_list[I][-1] = 1
    return


# 异常数据删除
def delete_error_data(my_list):
    # 数据最后一个没有处理，直接删掉
    my_list.pop()
    for temp in range(len(my_list)-1, -1, -1):
        if my_list[temp][-1] != 0:
            my_list.pop(temp)
    return


# 划段,运动学片段提取
def divided_data(my_list):
    run_data = []
    # 初始位置标志位
    flag = 1
    sum_zero = 0
    left_index = 0
    for i in range(len(my_list)-1):
        sum_zero = sum_zero + 1

        # 1-0更新
        if my_list[i][1] != 0 and my_list[i+1][1] == 0:
            sum_zero = 0
        # 0-1更新
        if my_list[i][1] == 0 and my_list[i+1][1] != 0:
            if flag != 1:
                run_data.append(my_list[left_index:(i-sum_zero//2)])
                left_index = i - sum_zero//2
        # 不同时间区
        flag = 0
        if my_list[i][14] != my_list[i+1][14]:
            sum_zero = 0
            left_index = i + 1
            flag = 1
    return run_data


# 运动学片段整理
# 1.片段量小于20s予以删除
def delete_dynamic_data(my_list):
    for i in range(len(my_list)-1, -1, -1):
        if len(my_list[i]) < 20:
            my_list.pop(i)
    return


# 特征量求解
# 1.平均速度Vm 总速度除以总时间 km/h
def average_speed_vm(my_list):
    total_speed = 0
    for i in range(len(my_list)):
        total_speed = my_list[i][1] + total_speed
    # total_time = my_list[-1][0]-my_list[0][0]
    total_time = len(my_list)
    if total_time == 0:
        total_time = 1
    return round(total_speed/total_time, 3)


# 2.平均行驶速度(不含怠速),Vmr,累加不为零的速度,并除以不为零的个数 km/h
def average_speed_vmr(my_list):
    n = 0
    total_speed = 0
    for i in range(len(my_list)):
        if my_list[i][1] != 0:
            n = n + 1
            total_speed = total_speed + my_list[i][1]
    if n == 0:
        return 0
    return round(total_speed/n, 3)


# 3.平均加速度Am,单位m/s2,所有加速度大于0.1的除以时间
def average_acc_am(my_list):
    n = 0
    total_acc = 0
    for i in range(len(my_list)-1):
        acc = my_list[i+1][1]-my_list[i][1]
        # 单位换算
        acc = acc/3.6
        if acc > 0.1:
            total_acc = total_acc + acc
            n = n + 1
    if n == 0:
        return 0
    return round(total_acc/n, 3)


# 4.平均减速度Dm,单位m/s2,所有减速度小于0.1的除以时间
def average_ace_dm(my_list):
    n = 0
    total_ace = 0
    for i in range(len(my_list)-1):
        ace = my_list[i+1][1]-my_list[i][1]
        ace = ace/3.6
        if ace < -0.1:
            total_ace = total_ace + ace
            n = n + 1
    if n == 0:
        return 0
    return round(total_ace/n, 3)


# 5.怠速时间比Tp,单位%,怠速占总时间的百分比
def percentage_tp(my_list):
    n = 0
    for i in range(len(my_list)):
        if 0.36 > my_list[i][1] > -0.36:
            n = n + 1
    return round(n/len(my_list), 3)


# 6.加速时间比Acp,单位%，加速时间占总时间百分比
def percentage_acp(my_list):
    n = 0
    for i in range(len(my_list)-1):
        acc = my_list[i+1][1]-my_list[i][1]
        acc = acc/3.6
        if acc > 0.1:
            n = n + 1
    return round(n/(len(my_list)-1), 5)


# 7.减速时间比Adp,单位%,减速时间占总时间百分比
def percentage_adp(my_list):
    n = 0
    for i in range(len(my_list)-1):
        ace = my_list[i+1][1]-my_list[i][1]
        ace = ace/3.6
        if ace < -0.1:
            n = n + 1
    return round(n/(len(my_list)-1), 5)


# 8.速度标准差　Vs　单位km/h 直接调用numpy模块
def standard_vs(my_list):
    item_list_vs = []
    for i in range(len(my_list)):
        item_list_vs.append(my_list[i][1])
    vs_std = numpy.std(item_list_vs, ddof=1)
    return round(vs_std, 3)


# 9.加速度标准差　As 单位m/s2 直接调用numpy模块
def standard_as(my_list):
    acct_list = []
    for i in range(len(my_list)-1):
        acc = my_list[i+1][1]-my_list[i][1]
        acc = acc/3.6
        if acc > 0.1 or acc < 0.1:
            acct_list.append(acc)
    acc_std = numpy.std(acct_list, ddof=1)
    return round(acc_std, 3)


# 10.运行时间　T 单位s
def sum_time(my_list):
    return len(my_list)


# 11.怠速时间Ti 单位s
def sum_ti(my_list):
    n = 0
    for i in range(len(my_list)):
        if my_list[i][1] == 0:
            n = n + 1
    return n


# 同一片段提取特征
def deal_single_part(my_list):
    deal_list = [average_speed_vm(my_list), average_speed_vmr(my_list), average_acc_am(my_list),
                 average_ace_dm(my_list),
                 standard_vs(my_list), standard_as(my_list)]
    return deal_list


# 总特征值提取,结果为片段特征值的均值
def all_part_mean(my_list):
    total = 0
    for i in range(len(my_list)):
        total = total + my_list[i][0]
    s0 = total/len(my_list)
    total = 0
    for i in range(len(my_list)):
        total = total + my_list[i][1]
    s1 = total/len(my_list)
    total = 0
    for i in range(len(my_list)):
        total = total + my_list[i][2]
    s2 = total/len(my_list)
    total = 0
    for i in range(len(my_list)):
        total = total + my_list[i][3]
    s3 = total/len(my_list)
    total = 0
    for i in range(len(my_list)):
        total = total + my_list[i][4]
    s4 = total/len(my_list)
    # total = 0
    # for i in range(len(my_list)):
    #     total = total + my_list[i][5]
    # s5 = total/len(my_list)
    # total = 0
    # for i in range(len(my_list)):
    #     total = total + my_list[i][6]
    # s6 = total/len(my_list)
    # total = 0
    # for i in range(len(my_list)):
    #     total = total + my_list[i][7]
    # s7 = total/len(my_list)
    total = 0
    for i in range(len(my_list)):
        total = total + my_list[i][5]
    s5 = total/len(my_list)
    # # 总运行时间
    # total = 0
    # for i in range(len(my_list)):
    #     total = total + my_list[i][6]
    # s6 = total/len(my_list)
    # # 总怠速时间
    # total = 0
    # for i in range(len(my_list)):
    #     total = total + my_list[i][7]
    # s7 = total/len(my_list)
    item_list_mean = [s0, s1, s2, s3, s4, s5]
    return item_list_mean


# 总特征值中位数提取
def all_part_median(my_list, l9=None):
    l0 = []
    for i in range(len(my_list)):
        l0.append(my_list[i][0])
    s0 = numpy.median(l0)
    l1 = []
    for i in range(len(my_list)):
        l1.append(my_list[i][1])
    s1 = numpy.median(l1)
    l2 = []
    for i in range(len(my_list)):
        l2.append(my_list[i][2])
    s2 = numpy.median(l2)
    l3 = []
    for i in range(len(my_list)):
        l3.append(my_list[i][3])
    s3 = numpy.median(l3)
    l4 = []
    for i in range(len(my_list)):
        l4.append(my_list[i][4])
    s4 = numpy.median(l4)
    # l5 = []
    # for i in range(len(my_list)):
    #     l5.append(my_list[i][5])
    # s5 = numpy.median(l5)
    # l6 = []
    # for i in range(len(my_list)):
    #     l6.append(my_list[i][6])
    # s6 = numpy.median(l6)
    # l7 = []
    # for i in range(len(my_list)):
    #     l7.append(my_list[i][7])
    # s7 = numpy.median(l7)
    l5 = []
    for i in range(len(my_list)):
        l5.append(my_list[i][5])
    s5 = numpy.median(l5)
    # l9 = []
    # for i in range(len(my_list)):
    #     l9.append(my_list[i][9])
    # s9 = numpy.median(l9)
    # l10 = []
    # for i in range(len(my_list)):
    #     l10.append(my_list[i][10])
    # s10 = numpy.median(l10)
    item_list_median = [s0, s1, s2, s3, s4, s5]
    return item_list_median


# 相似性计算，和总体平均值进行相似性计算,返回距离值,采用闵可夫斯基距离表示,距离越远,相似性越差
def similarity_value(solve_my_list, mean_my_list):
    p = len(solve_my_list)
    sum_value = 0
    for i in range(len(solve_my_list)):
        sum_value = sum_value + math.pow(abs(solve_my_list[i] - mean_my_list[i]), p)
    value = math.pow(sum_value, 1 / p)
    return value


# 合成工况序列,id为纵坐标,速度等
def solve_driving_cycle(my_list, my_res_data, Id):
    ind = 0
    item_solve_driving = []
    for i in range(len(my_list)):
        for j in range(len(my_res_data[my_list[i]])):
            ilise = [ind, my_res_data[my_list[i]][j][Id]]
            item_solve_driving.append(ilise)
            ind = ind + 1
    return item_solve_driving


# 读取数据
file_01 = "/home/ganggang/Desktop/x1.xlsx"
file_o1_open = xlrd.open_workbook(file_01)
data_01 = []
worksheet_01 = file_o1_open.sheet_by_name("原始数据1")
row_01 = worksheet_01.nrows
# 读入每一行数据
for i in range(row_01):
    data_01.append(worksheet_01.row_values(i))
# 去掉第一行表头数据
del data_01[0]
data_01_len = len(data_01)
# 将所有时间换为公秒
for i in range(data_01_len):
    # 临时时间字符串
    time_item = data_01[i][0]
    # 临时时间戳
    item = datetime.datetime.strptime(time_item, "%Y/%m/%d %H:%M:%S.%f.")
    # 临时浮点时间戳
    sec_float_item = time.mktime(item.timetuple())
    # 将公秒时间添加到队列末尾
    data_01[i][0] = sec_float_item
    # 增加一列表示时间片段的数据
    data_01[i].append(0)
    # 增加一列表示异常数据的
    data_01[i].append(0)
# 存储总数据量
save_file = open("data_01_save.txt", "w")
print("总数据量:", len(data_01))
save_file.write("总数据量: "+ str(len(data_01))+"\n")
total_num = len(data_01)
# 添加时间标记作为时间画区
divided_time(data_01)

# 数据保存
# save_data(data_01)

# 数据预处理
data_pre_process(data_01)

# 删除异常数据
delete_error_data(data_01)
print("正常数据量:", len(data_01))
save_file.write("正常数据量: "+str(len(data_01))+"\n")
total_no_error = len(data_01)

# 预处理后再次按时间分区
divided_time(data_01)
# save_data(data_01)

# 划分运动学划片段
res_data = divided_data(data_01)
# 运动学片段整理
delete_dynamic_data(res_data)
print("运动学片段总数:", len(res_data))
save_file.write("运动学片段总数: "+str(len(res_data))+"\n")
total_num_divided = len(res_data)
save_data_dynamic(res_data)
# print(deal_single_part(res_data[0]))
# 特征值存储到列表
special_value = []
for i in range(len(res_data)):
    special_value.append(deal_single_part(res_data[i]))
# 存储整体特征值数据
save_special_value(special_value)
# 总特征均值
all_mean = all_part_mean(special_value)
print("总特征值均值: ", all_mean)
save_file.write("总特征值均值: ")
for i in range(len(all_mean)):
    save_file.write(str(all_mean[i])+" ")
save_file.write("\n")
# 总特征值中位数
all_median = all_part_median(special_value)
print("总特征值中位数: ", all_median)
save_file.write("总特征值中位数: ")
for i in range(len(all_median)):
    save_file.write(str(all_median[i])+" ")
save_file.write("\n")
# 求解相似性到列表
similar_d = {}
for i in range(len(special_value)):
    similar_d[i] = similarity_value(special_value[i], all_mean)
# 安照距离值进行排序，距离越小相似性越好
sort_similar_list = sorted(similar_d.items(), key=lambda it: it[1])
# 求解相似性最好的序号
index_solve = []
sum_len_solve = 0
print("now", res_data[1][1])
for i in range(len(sort_similar_list)):
    if res_data[sort_similar_list[i][0]][0][1] >= 2 or res_data[sort_similar_list[i][0]][-1][1] > 3:
        continue
    sum_len_solve = sum_len_solve + len(res_data[sort_similar_list[i][0]])
    if sum_len_solve >= 1300:
        sum_len_solve = sum_len_solve - len(res_data[sort_similar_list[i][0]])
        break
    if sum_len_solve < 1300:
        index_solve.append(sort_similar_list[i][0])
    if sum_len_solve >= 1200:
        break
print("工况曲线长度: ", sum_len_solve)
save_file.write("工况曲线长度: "+str(sum_len_solve)+"\n")
print("工况曲线序列: ", index_solve)
save_file.write("工况曲线序列: ")
# 构建工况片段合成
driving_solve = solve_driving_cycle(index_solve, res_data, 1)
# 构建工况片段特征值提取
solve_driving_special_value = deal_single_part(driving_solve)
print("构建工况片段特征值: ", solve_driving_special_value)
save_file.write("构建工况片段特征值: ")
for i in range(len(solve_driving_special_value)):
    save_file.write(str(solve_driving_special_value[i])+" ")
save_file.write("\n")
# 误差值,与实验数据(均值)对比
list_error = []
for i in range(len(solve_driving_special_value)):
    err = abs(solve_driving_special_value[i] - all_mean[i])/abs(all_mean[i])
    list_error.append(err)
print("误差: ", list_error)
save_file.write("误差: ")
for i in range(len(list_error)):
    save_file.write(str(list_error[i])+" ")
save_file.write("\n")
# 存储工况速度与时间列表
save_file.close()
save_data(driving_solve)
