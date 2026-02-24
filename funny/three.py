stars = 1
levels = 20

for i in range(levels,0, -1):
  line = f"{'_'*i}{'*'*stars}{'_'*i}"
  stars = stars+2
  print(line)

cant_log = levels//2 if levels > 3 else 2

for i in range(1, cant_log):
  line_for_log = f"{'_'*levels}|{'_'*levels}"
  print(line_for_log)