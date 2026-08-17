"""Collatz Python Project

This program takes in a choice of xa+b
and outputs the two classic graphs, stopping times and max values

Orion Haunstrup
Winter Break 2018-2019
"""





global divergence_cutoff
divergence_cutoff = eval("1" + "0" * 100)
global fate_unknown_cutoff
fate_unknown_cutoff = 10000000


from math import log
import matplotlib.pyplot as plt


def create_colors_list():

    colors_list = ["xkcd:light grey", "xkcd:strong blue", "xkcd:sky blue",
                   "xkcd:purple", "xkcd:green", "xkcd:light green", "xkcd:brown",
                   "xkcd:red", "xkcd:teal", "xkcd:orange",
                   "xkcd:pink", "xkcd:magenta", "xkcd:yellow",
                   "xkcd:dark green", "xkcd:turquoise", "xkcd:lavender",
                   "xkcd:dark blue", "xkcd:tan", "xkcd:cyan",
                   "xkcd:melon", "xkcd:salmon", "xkcd:beige",
                   "xkcd:royal blue", "xkcd:hot pink"]
    ## A nice start

    infile = open("colors.txt", "r")
    FullData = infile.read()
    FullData = FullData.split("\n")
    infile.close()

    for line in FullData:
        line = line.split("\t")
        colors_list.append("xkcd:" + line[0])
    ## Then a whole bunch of random ones after

    snot_spot = colors_list.index("xkcd:snot")
    colors_list.remove("xkcd:snot")
            ##This color means fate_unknown
    colors_list.insert(snot_spot, colors_list[-1])
    colors_list = colors_list[:-1]

    neon_pink_spot = colors_list.index("xkcd:neon pink")
    colors_list.remove("xkcd:neon pink")
            ##This color means divergent
    colors_list.insert(neon_pink_spot, colors_list[-1])
    colors_list = colors_list[:-1]

    return colors_list




def ev_int(times_int, plus_int, n, known_loop_seeds):
    """ A function that fires a single hailstone. This version is the one
        to use when times & plus are integers. It returns a results list:
        [n, "loop", which_loop_seed, num_steps, max_value]
        or [n, "div"]
        or [n, "fate_unknown"]"""
    

    _max = n
    num_steps = 0
    b = n
    already_hit_its_loop_seed = False
    check_for_loop_checkpoint = 50
    nums_to_test_for_repeat = []
    on_the_heels_of_a_new_loop_seed = False
    collecting_dish_for_the_new_loop = []

    while True:

        if b in known_loop_seeds:
            if already_hit_its_loop_seed is False:
                result_which_loop_seed = b
                result_num_steps = num_steps
                already_hit_its_loop_seed = True
            elif already_hit_its_loop_seed is True:
                result_max_value = _max
                #This is here, in case you like start x3+1 at n = 2
                #You want it to return a max_value of 4, not 2
                return [n, "loop", result_which_loop_seed,
                        result_num_steps, result_max_value]

        if on_the_heels_of_a_new_loop_seed is False:
        ## A section seeing if it's in a new not-yet-discovered loop?
            if b in nums_to_test_for_repeat:
                ## Meaning that b is a repeat!
                on_the_heels_of_a_new_loop_seed = True
        else:
        ## A section discussing what to do if it IS in a new
                ## not-yet-discovered loop
            if b in collecting_dish_for_the_new_loop:
                ##Meaning that we've collected the full new loop
                new_loop_seed = min(collecting_dish_for_the_new_loop)
                known_loop_seeds.append(new_loop_seed)
                return ev_int(times_int, plus_int, n, known_loop_seeds)
            collecting_dish_for_the_new_loop.append(b)

        if num_steps == check_for_loop_checkpoint:
            nums_to_test_for_repeat.append(b)
            if len(nums_to_test_for_repeat) == 3:
                nums_to_test_for_repeat = nums_to_test_for_repeat[-2:]
                #For speed, we trim the list down to just 2 numbers to check
            if str(num_steps)[0] == "5":
                check_for_loop_checkpoint = check_for_loop_checkpoint * 4
            else:
                check_for_loop_checkpoint = check_for_loop_checkpoint * 25 // 10
            #check_for_loop_checkpoints = [50, 200, 500, 2000, 5000, 20000, ...]


        if b > divergence_cutoff:
            return [n, "div"]


        if num_steps > fate_unknown_cutoff:
            print(str(n) + " has fate_unknown")
            return [n, "fate_unknown"]


        # The simple integer version
        if b % 2 == 0:
            b = b//2
        else:
            b = (b*times_int+plus_int)//2*2

        num_steps += 1
        if b > _max:
            _max = b



def ev_non_int(times_str, plus_str, n, known_loop_seeds):
    """ A function that fires a single hailstone. This version is the one
        to use when either times or plus is a non-integer. To make sure there
        is never any rounding and so that it can run with extreme precision,
        all numbers are always kept in string or integer form, never evaluated
        as floats. Enter times_str and plus_str as strings with a decimal point.
        
        The function returns a results list:
        [n, "loop", which_loop_seed, num_steps, max_value]
        or [n, "div"]
        or [n, "fate_unknown"]"""


    # This is a section I added more recently
            # so the ev function will always be performing its
            # operations on integers... eliminating the
            # "rounding of enormous floats" problem that used to
            # occur past 10^12


    times_str_split = times_str.split(".")
    times_digits_after_decim = len(times_str_split[1])
    plus_str_split = plus_str.split(".")
    plus_digits_after_decim = len(plus_str_split[1])
    
    if times_digits_after_decim < plus_digits_after_decim:
        zeros_to_add = plus_digits_after_decim - times_digits_after_decim
        times_str_split[1] += zeros_to_add * "0"

    if plus_digits_after_decim < times_digits_after_decim:
        zeros_to_add = times_digits_after_decim - plus_digits_after_decim
        plus_str_split[1] += zeros_to_add * "0"

    decimal_places_moved = max(
        times_digits_after_decim, plus_digits_after_decim)

    if eval(times_str_split[0]) == 0:
        times_combined_str = times_str_split[0] + times_str_split[1]
        while times_combined_str[0] == "0":
            times_combined_str = times_combined_str[1:]
        times_as_an_int = eval(times_combined_str)
    else:
        times_as_an_int = eval(times_str_split[0] + times_str_split[1])
    if eval(plus_str_split[0]) == 0:
        plus_combined_str = plus_str_split[0] + plus_str_split[1]
        while plus_combined_str[0] == "0":
            plus_combined_str = plus_combined_str[1:]
        plus_as_an_int = eval(plus_combined_str)
    else:
        plus_as_an_int = eval(plus_str_split[0] + plus_str_split[1])
    new_divide = eval("2" + decimal_places_moved * "0")



    _max = n
    num_steps = 0
    b = n
    already_hit_its_loop_seed = False
    check_for_loop_checkpoint = 50
    nums_to_test_for_repeat = []
    on_the_heels_of_a_new_loop_seed = False
    collecting_dish_for_the_new_loop = []

    while True:

        if b in known_loop_seeds:
            if already_hit_its_loop_seed is False:
                result_which_loop_seed = b
                result_num_steps = num_steps
                already_hit_its_loop_seed = True
            elif already_hit_its_loop_seed is True:
                result_max_value = _max
                #This is here, in case you like start x3+1 at n = 2
                #You want it to return a max_value of 4, not 2
                return [n, "loop", result_which_loop_seed,
                        result_num_steps, result_max_value]

        if on_the_heels_of_a_new_loop_seed is False:
        ## A section seeing if it's in a new not-yet-discovered loop?
            if b in nums_to_test_for_repeat:
                ## Meaning that b is a repeat!
                on_the_heels_of_a_new_loop_seed = True
        else:
        ## A section discussing what to do if it IS in a new
                ## not-yet-discovered loop
            if b in collecting_dish_for_the_new_loop:
                ##Meaning that we've collected the full new loop
                new_loop_seed = min(collecting_dish_for_the_new_loop)
                known_loop_seeds.append(new_loop_seed)
                return ev_non_int(
                    times_str, plus_str, n, known_loop_seeds)
            collecting_dish_for_the_new_loop.append(b)

        if num_steps == check_for_loop_checkpoint:
            nums_to_test_for_repeat.append(b)
            if len(nums_to_test_for_repeat) == 3:
                nums_to_test_for_repeat = nums_to_test_for_repeat[-2:]
                #For speed, we trim the list down to just 2 numbers to check
            if str(num_steps)[0] == "5":
                check_for_loop_checkpoint = check_for_loop_checkpoint * 4
            else:
                check_for_loop_checkpoint = check_for_loop_checkpoint * 25 // 10
            #check_for_loop_checkpoints = [50, 200, 500, 2000, 5000, 20000, ...]


        if b > divergence_cutoff:
            return [n, "div"]


        if num_steps > fate_unknown_cutoff:
            print(str(n) + " has fate_unknown")
            return [n, "fate_unknown"]


        if b % 2 == 0:
            b = b//2
        else:
            b = (b*times_as_an_int+plus_as_an_int)//(new_divide)*2
                # This is the new version that always works in integers

        num_steps += 1
        if b > _max:
            _max = b



def main():

    print("This program takes in a choice of xa+b")
    print("    and outputs the two classic graphs,")
    print("          stopping times and max values")
    print()
    print("    Notes:")
    print("Entries are considered divergent if they rise above ", end="")
    if str(divergence_cutoff)[0] == "1" and len(
        str(divergence_cutoff)[1:]) == str(divergence_cutoff)[1:].count("0"):
        print("10^" + str(round(log(divergence_cutoff, 10))))
    else:
        print("10^" + str(log(divergence_cutoff, 10)))
    print()
    print("Entries are considered to be of 'unknown_fate' if")
    print("they go beyond", fate_unknown_cutoff,"steps undecisively.")
    print()

    print()
    print()
    print("Which Collatz Landscape would you like to explore?")
    times_str = input("xa+b, what is a?: ")
    plus_str = input("xa+b, what is b?: ")
    up_to_what_n = eval(input("Up to what value of n?: ")) + 1


    times_str_has_decimal = "." in times_str
    plus_str_has_decimal = "." in plus_str

    if times_str_has_decimal is False and plus_str_has_decimal is False:
        times, plus = eval(times_str), eval(plus_str)
        int_or_non = "int"
    else:
        ## Meaning that at least one of them is a float
        if times_str_has_decimal is False:
            times_str += ".0"
        if plus_str_has_decimal is False:
            plus_str += ".0"
        int_or_non = "non"
    

    print("Loading: ", end="")
    percent_loaded = 0
        

    ##Builds the Hailstone Dictionary
    hailstone_dictionary = {}
    known_loop_seeds = []
    for n in range(1, up_to_what_n):
        if int_or_non == "int":
            hailstone_dictionary[n] = ev_int(
                times, plus, n, known_loop_seeds)[1:]
        else:
            hailstone_dictionary[n] = ev_non_int(
                times_str, plus_str, n, known_loop_seeds)[1:]
        #Note that this function alters the known_loop_seeds list
        if n >= (percent_loaded / 10 + 1) * (up_to_what_n - 1) / 10:
            percent_loaded += 10
            print(str(percent_loaded) + "% ", end="")
            ##Shows the user how far along it is...


    ##Gets a little something ready to plot divergent entries
    max_max_value_up_to_that_n = 0
    max_stopping_time_up_to_that_n = 0
    all_divergent = False
    for n in range(1, up_to_what_n):
        if hailstone_dictionary[n][0] == "loop":
            if hailstone_dictionary[n][-1] > max_max_value_up_to_that_n:
                max_max_value_up_to_that_n = hailstone_dictionary[n][-1]
            if hailstone_dictionary[n][-2] > max_stopping_time_up_to_that_n:
                max_stopping_time_up_to_that_n = hailstone_dictionary[n][-2]
            all_divergent = True

    if all_divergent is False:
        max_stopping_time_up_to_that_n = 0
        max_max_value_up_to_that_n = 1


    ##Builds the various lists we'll need for plotting
    list_of_input_ns = []
    list_of_stopping_times = []
    list_of_max_values = []
    list_of_loops_encountered = []
    list_of_which_color = []
    colors_list = create_colors_list()

    for n in range(1, up_to_what_n):
        list_of_input_ns.append(n)
        if hailstone_dictionary[n][0] == "loop":
            list_of_stopping_times.append(hailstone_dictionary[n][-2])
            list_of_max_values.append(hailstone_dictionary[n][-1])
            loop_encountered = hailstone_dictionary[n][-3]
            if loop_encountered not in list_of_loops_encountered:
                list_of_loops_encountered.append(loop_encountered)
            list_of_which_color.append(
            colors_list[hailstone_dictionary[n][-3] % len(colors_list)])
        if hailstone_dictionary[n][0] == "div":
            list_of_stopping_times.append(max_stopping_time_up_to_that_n * 1.1)
                    ## a little above the maximum
            list_of_max_values.append(max_max_value_up_to_that_n * 1.1)
            list_of_which_color.append("xkcd:neon pink")
        if hailstone_dictionary[n][0] == "fate_unknown":
            list_of_stopping_times.append(max_stopping_time_up_to_that_n * 1.1)
                    ## a little above the maximum
            list_of_max_values.append(max_max_value_up_to_that_n * 1.1)
            list_of_which_color.append("xkcd:snot")

    ##Plots it all
    stopping_times_graph = plt.figure()
    plt.scatter(list_of_input_ns, list_of_stopping_times,
                s=1, c=list_of_which_color)
    plt.xlabel("input n")
    #plt.xscale('log')
    plt.ylabel("stopping times")
    if int_or_non == "int":
        plt.title("x" + str(times) + "+" + str(plus) + " Stopping Times Graph")
    else:
        if times_str_has_decimal is False:
            times_str = times_str[:-2]
        if plus_str_has_decimal is False:
            plus_str = plus_str[:-2]
        plt.title("x" + times_str + "+" + plus_str + " Stopping Times Graph")

    max_values_graph = plt.figure()
    plt.scatter(list_of_input_ns, list_of_max_values,
                s=2, c=list_of_which_color)
    plt.xlabel("input n")
    #plt.xscale('log')
    plt.ylabel("max values")
    #plt.yscale('log')
    plt.ylim(1, 2*up_to_what_n)
    if int_or_non == "int":
        plt.title("x" + str(times) + "+" + str(plus) + " Max Value Graph")
    else:
        plt.title("x" + times_str + "+" + plus_str + " Max Value Graph")

    known_loop_seeds.sort()
    print("\n\n\nWe found the following loop_seeds:")
    print(known_loop_seeds)

    plt.show()


main()
