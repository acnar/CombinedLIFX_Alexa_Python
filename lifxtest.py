from lifxlan.lifxlan import *

lan = LifxLAN()

power_level = 65535
percent = 100.0
brightness = 65535.0 * percent / 100
hue = 0
saturation = 0
kelvin = 4000
duration = 5000

#lights = lan.get_lights()
groups = lan.get_groups()
print("found %i groups\n" % len(groups))

for g in groups.items():
    name = g[0]
    print("found %i lights in group %s" % (len(g[1]), name))
    
lan.set_group("Living Room", (hue, saturation, brightness, kelvin), power_level, duration)

#percent = 90.0
#brightness = 65535.0 * percent / 100
#kelvin = 2500
#duration = 5000
#lan.set_hsbk_all_lights(0,0,brightness, kelvin, duration)


