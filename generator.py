# list_to_be_adjusted = [('navigation',),('navigation',)]  
# for adjust_item, *adjust_args in list_to_be_adjusted:
#     print(adjust_item, adjust_args)

# def abc(a):
#     return a

# 计算组合数C(n,3)
def comb3(n):
    if n < 3:
        return 0
    return n * (n-1) * (n-2) // 6

def encode(a, b, c, num):
    """
    将四元组(a,b,c,d)编码为唯一连续ID
    其中d = num - a - b - c
    ID范围: 0 到 C(num+3,3)-1
    """
    # 计算a部分的偏移量: ∑_{i=0}^{a-1} C(num-i+2, 2)
    total_a = comb3(num+3) - comb3(num-a+3)
    
    # 计算b部分的偏移量: ∑_{j=0}^{b-1} (num-a-j+1)
    total_b = (num - a + 1) * b - b*(b-1)//2
    
    return total_a + total_b + c


with open("generator.txt", "w",encoding='utf-8') as file:

    for num in range(13):
        ava_bank = 12
        ava_law = 12
        ava_engineering = 12
        ava_medical = 12    
        start_id = sum(comb3(i) for i in range(3,num+3))
        available_immediate_action_ids = []
        for i in range(min(num,ava_bank)+1):
            for j in range(min(num-i,ava_law)+1):
                for k in range(min(num-i-j,ava_engineering)+1):
                    for l in range(min(num-i-j-k,ava_medical)+1):
                        if i+j+k+l == num:
                            file.write(f"\t\t\t{10000+start_id+encode(i,j,k,num)}: ")
                            file.write("{")
                            file.write(f"'action': 'select_books',   'args': ('use', {(i,j,k,l)}),\t'description': '立即行动: 选择银行、法律、工程、医疗书分别{i},{j},{k},{l}本'")
                            file.write("},\n")

    file.write('\n')

    for num in range(13):
        ava_bank = 12
        ava_law = 12
        ava_engineering = 12
        ava_medical = 12    
        start_id = sum(comb3(i) for i in range(3,num+3))
        available_immediate_action_ids = []
        for i in range(min(num,ava_bank)+1):
            for j in range(min(num-i,ava_law)+1):
                for k in range(min(num-i-j,ava_engineering)+1):
                    for l in range(min(num-i-j-k,ava_medical)+1):
                        if i+j+k+l == num:
                            file.write(f"\t\t\t{11820+start_id+encode(i,j,k,num)}: ")
                            file.write("{")
                            file.write(f"'action': 'select_books',   'args': ('get', {(i,j,k,l)}),\t'description': '立即行动: 选择银行、法律、工程、医疗书分别{i},{j},{k},{l}本'")
                            file.write("},\n")

    file.write('\n')

    for num in range(13):
        ava_bank = 12
        ava_law = 12
        ava_engineering = 12
        ava_medical = 12
        start_id = sum(comb3(i) for i in range(3,num+3))
        available_immediate_action_ids = []
        for i in range(min(num,ava_bank)+1):
            for j in range(min(num-i,ava_law)+1):
                for k in range(min(num-i-j,ava_engineering)+1):
                    for l in range(min(num-i-j-k,ava_medical)+1):
                        if i+j+k+l == num:
                            file.write(f"\t\t\t{13640+start_id+encode(i,j,k,num)}: ")
                            file.write("{")
                            file.write(f"'action': 'select_tracks',  'args': {(i,j,k,l)},\t'description': '立即行动: 选择银行、法律、工程、医疗轨分别推进{i},{j},{k},{l}格'")
                            file.write("},\n")