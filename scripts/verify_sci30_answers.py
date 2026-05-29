"""Re-compute every numerical answer in the Sci30 Unit C review pack and
compare against the values stated in build_sci30_unitc_review.py."""
from math import sqrt

G = 6.67e-11
k = 8.99e9
g_E = 9.81
M_E = 5.98e24
R_E = 6.37e6
M_S = 1.99e30
AU = 1.50e11
c = 3.00e8

results = []

def rec(label, computed, stated):
    results.append((label, computed, stated))


# Q1.1
F = (100. + 27) * 1.0e-3
rec("1.1 F (loaded Philae on 67P)", F, "0.13 N (1.0e-3 has 2 sf -> 0.13)")

# Q1.2
F_mars = 1.025e3 * 3.71
F_earth = 1.025e3 * 9.81
diff = F_earth - F_mars
rec("1.2a F on Mars", F_mars, "3.80e3 N")
rec("1.2b F on Earth", F_earth, "1.01e4 N")
rec("1.2c diff", diff, "6.25e3 N")

# Q1.3
m13 = 1.85e2
F_e = m13 * 9.81
F_m = m13 * 1.62
F_b = m13 * 7.8e-5
ratio = F_m/F_e * 100
rec("1.3a F Earth (185 kg)", F_e, "1.81e3 N")
rec("1.3b F Moon", F_m, "3.00e2 N")
rec("1.3c F Bennu", F_b, "1.4e-2 N")
rec("1.3d Moon%", ratio, "16.5 %")

# Q2.1
r_iss = R_E + 4.20e5
g_iss = G*M_E/r_iss**2
rec("2.1 g at ISS", g_iss, "8.65 N/kg")

# Q2.2
g_1au = G*M_S/AU**2
g_05au = G*M_S/(0.5*AU)**2
rec("2.2a g(1 AU)", g_1au, "5.90e-3 N/kg")
rec("2.2b g(0.5 AU)", g_05au, "2.36e-2 N/kg")
rec("2.2c ratio", g_05au/g_1au, "4.00")

# Q2.3
g_67p = G*1.0e13/(3.00e4)**2
F_ros = 1.30e3 * g_67p
rec("2.3a g near Rosetta", g_67p, "7.4e-7 N/kg")
rec("2.3b F on Rosetta", F_ros, "9.6e-4 N")

# Q3.1
E31 = k*5.00e-9/(0.500)**2
rec("3.1 E (Moon dust)", E31, "1.80e2 N/C")

# Q3.2
E32a = k*8.0e-5/(0.10)**2
E32b = k*8.0e-5/(0.30)**2
rec("3.2a E at 0.10 m", E32a, "7.2e7 N/C")
rec("3.2b E at 0.30 m", E32b, "8.0e6 N/C")
rec("3.2c ratio", E32a/E32b, "9.0")

# Q3.3
E33a = k*2.50e-4/(100.)**2
E33b = k*2.50e-4/(300.)**2
r_target = sqrt(k*2.50e-4/1.00e2)
rec("3.3a E at 100 m", E33a, "2.25e2 N/C")
rec("3.3b E at 300 m", E33b, "25.0 N/C")
rec("3.3c r where E=100 N/C", r_target, "1.50e2 m (150 m)")

# Q4.1
R41a = 12.0/0.50
I41b = 24.0/R41a
rec("4.1a R lamp", R41a, "24 ohm")
rec("4.1b I doubled", I41b, "1.0 A")

# Q4.2
I42a = 12.0/25.0
I42b = 12.0/40.0
rec("4.2a I clean", I42a, "0.480 A")
rec("4.2b I dusty", I42b, "0.300 A")

# Q4.3
R_orig = 28/5.0
R_new = 0.5*R_orig
I_new = 28/R_new
rec("4.3a R original", R_orig, "5.6 ohm")
rec("4.3b R new", R_new, "2.8 ohm")
rec("4.3c I new", I_new, "10. A (1.0e1)")

# Q5.1
RT51 = 4*30.
I51 = 12.0/RT51
rec("5.1a R_T", RT51, "1.2e2 ohm (120)")
rec("5.1b I", I51, "0.10 A")

# Q5.2
RT52 = 8*64.0
I52 = 24.0/RT52
rec("5.2a R_T", RT52, "512 ohm")
rec("5.2b I", I52, "4.69e-2 A")

# Q5.3
RT53 = 20+50+80
I53 = 30.0/RT53
V1 = I53*20.0; V2 = I53*50.0; V3 = I53*80.0
rec("5.3a R_T", RT53, "150.0 ohm")
rec("5.3b I", I53, "0.200 A")
rec("5.3c V1+V2+V3", V1+V2+V3, "30.0 V")

# Q6.1
RT61 = 1/(1/100. + 1/100.)
I61 = 24.0/RT61
rec("6.1a R_T", RT61, "50. ohm")
rec("6.1b I_total", I61, "0.480 A")

# Q6.2
RT62 = 1/(1/60.+1/30.+1/20.)
I62 = 12.0/RT62
rec("6.2a R_T", RT62, "10. ohm")
rec("6.2b I_total", I62, "1.2 A")

# Q6.3
RT63 = 96/5
I63 = 120/RT63
I_each = 120/96
rec("6.3a R_T", RT63, "19.2 ohm")
rec("6.3b I_total", I63, "6.25 A")
rec("6.3c I_each", I_each, "1.25 A")
rec("6.3d 5*I_each", 5*I_each, "6.25 A")

# Q7.1
P71a = 12.0*28.0
P71b = 8.0*28.0
rec("7.1a P_active", P71a, "336 W")
rec("7.1b P_low", P71b, "224 W")

# Q7.2
P72 = 2.5**2 * 4.0
V72 = 2.5*4.0
P72c = 2.5*V72
rec("7.2a P=I^2R", P72, "25 W")
rec("7.2b V=IR", V72, "10. V")
rec("7.2c P=IV check", P72c, "25 W")

# Q7.3
I73 = 28.0/7.00
P73a = I73*28.0
P73b = I73**2 * 7.00
rec("7.3a I", I73, "4.00 A")
rec("7.3b P=IV", P73a, "112 W")
rec("7.3c P=I^2R", P73b, "112 W")

# Q8.1
t81 = 4.00*3600
E81J = 50.*t81
E81kwh = 0.050*4.00
rec("8.1a E in J", E81J, "7.2e5 J")
rec("8.1b E in kWh", E81kwh, "0.20 kWh")
rec("8.1c kWh*3.6e6", E81kwh*3.6e6, "7.2e5 J check")

# Q8.2
E_day = 0.200*8.00
E_year = E_day*365
E_year_J = E_year*3.6e6
rec("8.2a E_day", E_day, "1.60 kWh")
rec("8.2b E_year", E_year, "584 kWh")
rec("8.2c E_year_J", E_year_J, "2.10e9 J")

# Q8.3
hrs = 365*24
E81 = 0.0080*hrs
cost81 = E81*0.124
E82 = 0.0020*hrs
cost82 = E82*0.124
sav = cost81 - cost82
rec("8.3a E1 yr", E81, "70 kWh")
rec("8.3b cost1 yr", cost81, "$8.7")
rec("8.3c E2 yr", E82, "18 kWh")
rec("8.3d cost2 yr", cost82, "$2.2")
rec("8.3e savings", sav, "$6.5")

# Q9.1
N_s91 = 125 * 12000/240
I_s91 = 25.0 * 240/12000
rec("9.1a N_s", N_s91, "6250 turns")
rec("9.1b I_s", I_s91, "0.500 A")

# Q9.2
N_s92 = 560*5.00/28.0
I_s92 = 0.500*560/N_s92
rec("9.2a N_s", N_s92, "100. turns")
rec("9.2b I_s", I_s92, "2.80 A")

# Q9.3
N_s93 = 80*7200/240
I_s93 = 100.*240/7200
P_in = 240*100.
P_out = 7200*I_s93
rec("9.3a N_s", N_s93, "2400 turns")
rec("9.3b I_s", I_s93, "3.33 A")
rec("9.3c P_in", P_in, "2.40e4 W")
rec("9.3d P_out", P_out, "2.40e4 W (within rounding)")

# Q10.1
lam = c/6.00e14
rec("10.1 lambda", lam, "5.00e-7 m (500 nm)")

# Q10.2
f1 = c/0.130
f2 = c/0.260
rec("10.2a f1", f1, "2.31e9 Hz")
rec("10.2b f2", f2, "1.15e9 Hz")

# Q10.3
f_lab = c/6.56e-7
f_obs = c/6.60e-7
df = f_lab - f_obs
rec("10.3a f_lab", f_lab, "4.57e14 Hz")
rec("10.3b f_obs", f_obs, "4.55e14 Hz")
rec("10.3c df", df, "~2e12 Hz")


for label, computed, stated in results:
    if isinstance(computed, float):
        print(f"{label:40s} computed={computed:.4g}    stated={stated}")
    else:
        print(f"{label:40s} computed={computed}    stated={stated}")
