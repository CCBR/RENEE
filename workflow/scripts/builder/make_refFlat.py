# while read a b c d e f g h i j k l;do
# a1=`grep -m1 $d hs38d1.annotate.isoforms.txt|awk '{print $2}'`;
# i1=`python add2all.py $l $b|sed "s/ //g"`
# j1=`python sum_lists.py $i1 $k|sed "s/ //g"`
# echo -e "$a1\t$d\t$a\t$f\t$b\t$c\t$g\t$h\t$i1\t$j1"
# done< genes.ref.bed|head


def add2all(a, b):
    lst = a.strip().split(",")
    lst.pop(-1)
    return ",".join([str(int(x) + int(b)) for x in lst]) + ","


def sum_lists(a, b):
    lst1 = a.strip().split(",")
    lst1.pop(-1)
    lst2 = b.strip().split(",")
    lst2.pop(-1)
    return ",".join([str(int(a) + int(b)) for a, b in zip(lst1, lst2)]) + ","


tid2genename = {
    a[0]: a[1]
    for a in map(
        lambda x: x.strip().split("  "), open("annotate.isoforms.txt").readlines()
    )
}

for line in map(lambda x: x.strip().split("\t"), open("genes.ref.bed").readlines()):
    newl = []
    newl.append(tid2genename['"' + line[3] + '"'].strip('"'))
    newl.append(line[3])
    newl.append(line[0])
    newl.append(line[5])
    newl.append(line[1])
    newl.append(line[2])
    newl.append(line[6])
    newl.append(line[7])
    newl.append(line[9])
    lst = add2all(line[11], line[1])
    newl.append(lst)
    newl.append(sum_lists(line[10], lst))
    print("\t".join(newl))
