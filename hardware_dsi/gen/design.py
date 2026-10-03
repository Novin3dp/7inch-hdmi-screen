"""
Single source of truth for the AT070TN92 Raspberry Pi DSI driver board.

Everything (schematic, PCB netlist, BOM) is generated from the PARTS list below.
Pin numbers refer to the KiCad library symbol / footprint pad numbers.

Board function
  * Raspberry Pi DSI (15-pin 1 mm, 2 lanes) -> ICN6211 (MIPI DSI -> 24-bit TTL RGB, DE mode)
    -> AT070TN92 50-pin FPC.  The ICN6211 is configured by the Linux driver
    (drivers/gpu/drm/bridge/chipone-icn6211.c) over DSI; no microcontroller on the board.
  * Panel bias: TPS61040 boost (AVDD 10.4 V) + charge pumps (VGH +16 V, VGL -6.8 V)
                + LM321 VCOM buffer with trimmer (2.55 .. 4.5 V)   (same as the HDMI board)
  * Backlight: TPS61165 constant-current boost, 182 mA, PWM/on-off from a Pi GPIO
  * GT915 touch on the DSI connector's I2C bus (i2c_csi_dsi), INT/RST to Pi GPIOs,
    read by the Linux goodix driver.
  * 5 V and four GPIOs come from the Pi 40-pin header through J2 (the DSI cable has no 5 V).
  * Power sequencing in hardware from DSI_EN (the bridge enable GPIO driven by Linux):
    DSI_EN high -> panel RESET released (1 ms) -> bias on (RC ~50 ms).
"""

NC = None  # explicit no-connect


class Part:
    def __init__(self, ref, lib, sym, value, fp, pins, sheet, mpn="", lcsc="", dnp=False, desc=""):
        self.ref, self.lib, self.sym, self.value, self.fp = ref, lib, sym, value, fp
        self.pins = {str(k): v for k, v in pins.items()}
        self.sheet, self.mpn, self.lcsc, self.dnp, self.desc = sheet, mpn, lcsc, dnp, desc


PARTS = []


def P(*a, **k):
    p = Part(*a, **k)
    assert p.ref not in [q.ref for q in PARTS], p.ref
    PARTS.append(p)
    return p


# ---------------------------------------------------------------- footprints
F_R0603 = "Resistor_SMD:R_0603_1608Metric"
F_R0805 = "Resistor_SMD:R_0805_2012Metric"
F_C0603 = "Capacitor_SMD:C_0603_1608Metric"
F_C0805 = "Capacitor_SMD:C_0805_2012Metric"
F_C1206 = "Capacitor_SMD:C_1206_3216Metric"
F_SOT23 = "Package_TO_SOT_SMD:SOT-23"
F_SOT235 = "Package_TO_SOT_SMD:SOT-23-5"
F_SOT236 = "Package_TO_SOT_SMD:SOT-23-6"
F_SOT223 = "Package_TO_SOT_SMD:SOT-223-3_TabPin2"
F_SOD123 = "Diode_SMD:D_SOD-123"
F_SOD323 = "Diode_SMD:D_SOD-323"
F_LED0603 = "LED_SMD:LED_0603_1608Metric"
F_TP = "TestPoint:TestPoint_Pad_D1.0mm"


def R(ref, val, a, b, sheet, fp=F_R0603, mpn="", lcsc="", dnp=False):
    return P(ref, "Device", "R", val, fp, {1: a, 2: b}, sheet, mpn=mpn, lcsc=lcsc, dnp=dnp)


def C(ref, val, a, b, sheet, fp=F_C0603, mpn="", lcsc="", dnp=False):
    return P(ref, "Device", "C", val, fp, {1: a, 2: b}, sheet, mpn=mpn, lcsc=lcsc, dnp=dnp)


# common LCSC basic parts (JLCPCB "basic" library)
L_100N = "C14663"    # 100nF 0603 X7R 50V
L_1U = "C15849"      # 1uF 0603 X5R 25V
L_10U0603 = "C19702"  # 10uF 0603 X5R 10V
L_22U0805 = "C45783"  # 22uF 0805 X5R 25V
L_10K = "C25804"     # 0603 1%
L_4K7 = "C23162"
L_1K = "C21190"
L_100K = "C25803"

# =====================================================================
# Sheet 1: Pi GPIO-header connector (5 V + control lines) and 3.3 V
# =====================================================================
S = "power"
P("J2", "Connector_Generic", "Conn_01x08", "to Pi 40-pin header",
  "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
  {1: "+5V_IN", 2: "+5V_IN", 3: "GND", 4: "GND", 5: "DSI_EN", 6: "TP_INT", 7: "TP_RST", 8: "BL_PWM"}, S,
  mpn="1x8 2.54mm pin header", desc="5V: Pi pins 2/4, GND: 6/9, DSI_EN GPIO, TP_INT, TP_RST, BL_PWM (GPIO18)")
P("F1", "Device", "Polyfuse_Small", "PTC 1.1A hold", "Fuse:Fuse_1206_3216Metric",
  {1: "+5V_IN", 2: "+5V"}, S, mpn="1206L110/16 (or BSMD1206-110)")
C("C1", "22uF", "+5V", "GND", S, fp=F_C0805, lcsc=L_22U0805)
C("C2", "100nF", "+5V", "GND", S, lcsc=L_100N)
P("U2", "Regulator_Linear", "AMS1117-3.3", "AMS1117-3.3", F_SOT223,
  {1: "GND", 2: "+3V3", 3: "+5V"}, S, mpn="AMS1117-3.3", lcsc="C6186")
C("C3", "22uF", "+3V3", "GND", S, fp=F_C0805, lcsc=L_22U0805)
C("C4", "100nF", "+3V3", "GND", S, lcsc=L_100N)
P("D7", "Device", "LED", "green", F_LED0603, {1: "LED_K", 2: "+3V3"}, S, lcsc="C72043")
R("R34", "1k", "LED_K", "GND", S, lcsc=L_1K)
for i, n in enumerate(["+5V", "+3V3", "AVDD", "VGH", "VGL", "VCOM", "GND"]):
    P("TP%d" % (i + 1), "Connector", "TestPoint", n, F_TP, {1: n}, S)

# =====================================================================
# Sheet 2: DSI input and ICN6211 bridge
# =====================================================================
S = "dsi"
# Raspberry Pi 15-pin DSI pinout (Pi 3/4 display connector, same numbering on both cable ends).
# Pins 14/15 (Pi 3V3) and pin 1 (GND, mirror of 15) are left open: a cable inserted the wrong way
# round then cannot short the Pi 3V3 to GND.  The board runs from the 5 V of the GPIO header.
P("J1", "Connector_Generic_MountingPin", "Conn_01x15_MountingPin", "Pi DSI 15P 1.0mm FPC",
  "lcd_dsi:FPC_15P_P1.0_PiDSI",
  {1: NC, 2: "DSI_D1_N", 3: "DSI_D1_P", 4: "GND", 5: "DSI_CK_N", 6: "DSI_CK_P", 7: "GND",
   8: "DSI_D0_N", 9: "DSI_D0_P", 10: "GND", 11: "DSI_SCL", 12: "DSI_SDA", 13: "GND", 14: NC, 15: NC,
   "MP": "GND"}, S, mpn="1.0mm 15P FPC, dual contact (TE 1-84953-5 land pattern)")
ICN = {
    1: "LCD_B2", 2: "LCD_B3", 3: "+3V3", 4: "LCD_B4", 5: "LCD_B5", 6: "LCD_B6", 7: "LCD_B7",
    8: "GND", 9: "DSI_SCL", 10: "DSI_SDA", 11: "DSI_EN", 12: "+3V3", 13: "GND",
    14: "DSI_D0_P", 15: "DSI_D0_N", 16: "DSI_D1_P", 17: "DSI_D1_N", 18: "DSI_CK_P", 19: "DSI_CK_N",
    20: NC, 21: NC, 22: NC, 23: NC, 24: "+3V3", 25: "ICN_PCLK", 26: NC, 27: NC, 28: "LCD_DE",
    29: "LCD_R0", 30: "LCD_R1", 31: "LCD_R2", 32: "LCD_R3", 33: "LCD_R4", 34: "LCD_R5", 35: "GND",
    36: "LCD_R6", 37: "LCD_R7", 38: "LCD_G0", 39: "LCD_G1", 40: "ICN_VCORE", 41: "LCD_G2",
    42: "LCD_G3", 43: "LCD_G4", 44: "LCD_G5", 45: "LCD_G6", 46: "LCD_G7", 47: "LCD_B0", 48: "LCD_B1",
    49: "GND",
}
P("U1", "lcd_dsi", "ICN6211", "ICN6211", "lcd_dsi:QFN-48-1EP_6x6mm_P0.4mm_EP4.2x4.2mm_Vias0.3",
  ICN, S, mpn="ICN6211 (Chipone)", lcsc="C246085", desc="MIPI DSI -> RGB888 bridge")
R("R1", "100k", "DSI_EN", "GND", S, lcsc=L_100K)          # bridge held in reset until Linux enables it
R("R2", "4.7k", "DSI_SCL", "+3V3", S, lcsc=L_4K7)
R("R3", "4.7k", "DSI_SDA", "+3V3", S, lcsc=L_4K7)
R("R4", "22R", "ICN_PCLK", "LCD_DCLK", S, lcsc="C23345")
# supply decoupling at the pins (VDD1 MIPI RX, VDD2 PLL, VDD3 RGB out) + VCORE (1uF + 10nF, the
# datasheet minimum; both sit right at pin 40)
C("C5", "100nF", "+3V3", "GND", S, lcsc=L_100N)    # pin 12
C("C6", "100nF", "+3V3", "GND", S, lcsc=L_100N)    # pin 24
C("C7", "100nF", "+3V3", "GND", S, lcsc=L_100N)    # pin 3
C("C8", "10uF", "+3V3", "GND", S, lcsc=L_10U0603)
C("C9", "1uF", "ICN_VCORE", "GND", S, lcsc=L_1U)
C("C11", "10nF", "ICN_VCORE", "GND", S, lcsc="C57112")

# =====================================================================
# Sheet 3: LCD panel connector, panel bias, VCOM, backlight
# =====================================================================
S = "panel"
FPC = {1: "VLED_A", 2: "VLED_A", 3: "VLED_K", 4: "VLED_K", 5: "GND", 6: "VCOM", 7: "+3V3",
       8: "LCD_MODE", 9: "LCD_DE", 10: "LCD_VS", 11: "LCD_HS",
       36: "GND", 37: "LCD_DCLK", 38: "GND", 39: "LCD_LR", 40: "LCD_UD", 41: "VGH", 42: "VGL",
       43: "AVDD", 44: "LCD_RST", 45: NC, 46: "VCOM", 47: "LCD_DITHB", 48: "GND", 49: NC, 50: NC}
for i in range(8):
    FPC[12 + i] = "LCD_B%d" % (7 - i)
    FPC[20 + i] = "LCD_G%d" % (7 - i)
    FPC[28 + i] = "LCD_R%d" % (7 - i)
FPC["MP"] = "GND"
P("J3", "Connector_Generic_MountingPin", "Conn_01x50_MountingPin", "AT070TN92 FPC (0.5mm 50P, top contact)",
  "lcd_dsi:FPC_50P_P0.5_TopContact_AT070TN92", FPC, S,
  mpn="Hirose FH12A-50S-0.5SH(55) (top contact)",
  desc="pad numbers == panel FPC pin numbers")
R("R15", "10k", "LCD_MODE", "+3V3", S, lcsc=L_10K)     # DE mode
R("R16", "10k", "LCD_HS", "+3V3", S, lcsc=L_10K)       # HS/VS high in DE mode
R("R17", "10k", "LCD_VS", "+3V3", S, lcsc=L_10K)
R("R18", "10k", "LCD_DITHB", "+3V3", S, lcsc=L_10K)    # dithering off (24-bit input)
R("R19", "10k", "LCD_LR", "+3V3", S, lcsc=L_10K)       # left->right  (swap to GND to mirror)
R("R20", "10k", "LCD_UD", "GND", S, lcsc=L_10K)        # up->down     (swap to +3V3 to flip)
# panel reset released ~1 ms after DSI_EN, bias ~50 ms later (RC), both drop with DSI_EN
R("R21", "10k", "DSI_EN", "LCD_RST", S, lcsc=L_10K)
C("C13", "100nF", "LCD_RST", "GND", S, lcsc=L_100N)
R("R5", "10k", "DSI_EN", "BIAS_EN", S, lcsc=L_10K)
C("C14", "4.7uF", "BIAS_EN", "GND", S, lcsc="C19666")
C("C27", "1uF", "+3V3", "GND", S, lcsc=L_1U)
C("C28", "100nF", "+3V3", "GND", S, lcsc=L_100N)

# --- bias supply, switched by BIAS_EN
P("Q1", "Transistor_FET", "AO3401A", "AO3401A", F_SOT23, {1: "BIAS_G", 2: "+5V", 3: "BOOST_IN"}, S,
  mpn="AO3401A", lcsc="C15127")
R("R22", "100k", "BIAS_G", "+5V", S, lcsc=L_100K)
P("Q2", "Transistor_FET", "2N7002", "2N7002", F_SOT23, {1: "BIAS_EN", 2: "GND", 3: "BIAS_G"}, S,
  mpn="2N7002", lcsc="C8545")
R("R23", "100k", "BIAS_EN", "GND", S, lcsc=L_100K)
C("C29", "10uF", "BOOST_IN", "GND", S, fp=F_C0603, lcsc=L_10U0603)
P("U7", "Regulator_Switching", "TPS61040DBV", "TPS61040", F_SOT235,
  {1: "AVDD_SW", 2: "GND", 3: "AVDD_FB", 4: "BOOST_IN", 5: "BOOST_IN"}, S,
  mpn="TPS61040DBVR", lcsc="C7722")
P("L1", "Device", "L", "10uH 0.6A", "Inductor_SMD:L_Taiyo-Yuden_NR-30xx",
  {1: "BOOST_IN", 2: "AVDD_SW"}, S, mpn="NR3015T100M")
P("D1", "Device", "D_Schottky", "MBR0530", F_SOD123, {1: "AVDD", 2: "AVDD_SW"}, S,
  mpn="MBR0530T1G", lcsc="C80521")
R("R24", "750k 1%", "AVDD", "AVDD_FB", S, lcsc="C25813")
R("R25", "100k 1%", "AVDD_FB", "GND", S, lcsc=L_100K)
C("C30", "10pF", "AVDD", "AVDD_FB", S, lcsc="C32949")
C("C31", "4.7uF 25V", "AVDD", "GND", S, fp=F_C0805, lcsc="C1779")
C("C32", "4.7uF 25V", "AVDD", "GND", S, fp=F_C0805, lcsc="C1779")
# VGH: charge-pump doubler from the switch node, zener regulated to 16 V
C("C33", "100nF 50V", "AVDD_SW", "CP_P", S, fp=F_C0603, lcsc="C14663")
P("D2", "Diode", "BAT54S", "BAT54S", F_SOT23, {1: "AVDD", 3: "CP_P", 2: "VGH_RAW"}, S,
  mpn="BAT54S", lcsc="C19726")
C("C34", "1uF 50V", "VGH_RAW", "GND", S, fp=F_C0805, lcsc="C28323")
R("R26", "2.2k", "VGH_RAW", "VGH", S, lcsc="C25879")
P("D3", "Device", "D_Zener", "16V 2%", F_SOD323, {1: "VGH", 2: "GND"}, S, mpn="BZX384-B16")
C("C35", "4.7uF 25V", "VGH", "GND", S, fp=F_C0805, lcsc="C1779")
# VGL: inverting charge pump, zener regulated to -6.8 V
C("C36", "100nF 50V", "AVDD_SW", "CP_N", S, fp=F_C0603, lcsc="C14663")
P("D4", "Diode", "BAT54S", "BAT54S", F_SOT23, {1: "VGL_RAW", 3: "CP_N", 2: "GND"}, S,
  mpn="BAT54S", lcsc="C19726")
C("C37", "1uF 25V", "VGL_RAW", "GND", S, fp=F_C0603, lcsc="C15849")
R("R27", "2.2k", "VGL_RAW", "VGL", S, lcsc="C25879")
P("D5", "Device", "D_Zener", "6.8V 2%", F_SOD323, {1: "GND", 2: "VGL"}, S, mpn="BZX384-B6V8")
C("C38", "1uF 25V", "VGL", "GND", S, fp=F_C0603, lcsc="C15849")
# VCOM buffer
R("R28", "30k 1%", "AVDD", "VCOM_TOP", S, lcsc="C22984")
P("RV1", "Device", "R_Potentiometer", "10k trim (VCOM)", "Potentiometer_SMD:Potentiometer_Bourns_TC33X_Vertical",
  {1: "VCOM_TOP", 2: "VCOM_SET", 3: "VCOM_BOT"}, S, mpn="Bourns TC33X-2-103E", lcsc="C720540")
R("R29", "13k 1%", "VCOM_BOT", "GND", S)
C("C39", "100nF", "VCOM_SET", "GND", S, lcsc=L_100N)
P("U8", "Amplifier_Operational", "LM321", "LM321", F_SOT235,
  {1: "VCOM_SET", 2: "GND", 3: "VCOM_BUF", 4: "VCOM_BUF", 5: "AVDD"}, S, mpn="LM321MFX", lcsc="C8106")
R("R30", "33R", "VCOM_BUF", "VCOM", S, lcsc="C25105")
C("C40", "1uF", "VCOM", "GND", S, lcsc=L_1U)
C("C41", "100nF", "AVDD", "GND", S, lcsc=L_100N)
# --- LED backlight: 9.3 V / 180 mA string, TPS61165 constant current
P("U9", "Driver_LED", "TPS61165DBV", "TPS61165", F_SOT236,
  {1: "+5V", 2: "BL_PWM", 3: "BL_SW", 4: "GND", 5: "BL_COMP", 6: "VLED_K"}, S,
  mpn="TPS61165DBVR", lcsc="C125979")
P("L2", "Device", "L", "10uH 1.2A", "Inductor_SMD:L_Taiyo-Yuden_NR-40xx",
  {1: "+5V", 2: "BL_SW"}, S, mpn="NR4018T100M")
P("D6", "Device", "D_Schottky", "MBR0560", F_SOD123, {1: "VLED_A", 2: "BL_SW"}, S,
  mpn="MBR0560T1G", lcsc="C22452")
C("C42", "2.2uF 50V", "VLED_A", "GND", S, fp=F_C1206, lcsc="C13832")
C("C43", "10uF", "+5V", "GND", S, fp=F_C0603, lcsc=L_10U0603)
C("C44", "220nF", "BL_COMP", "GND", S, lcsc="C16772")
R("R31", "1.1R 1%", "VLED_K", "GND", S, fp=F_R0805, lcsc="C17520")
# backlight on by default (wire not connected); a Pi GPIO / PWM overrides the 10k pull-up
R("R32", "10k", "BL_PWM", "+3V3", S, lcsc=L_10K)

# touch panel (GT915 on the touch-panel FPC) on the DSI-connector I2C bus
TP = {1: "GND", 2: "+3V3", 3: "TP_INT", 4: "DSI_SCL", 5: "DSI_SDA", 6: "TP_RST"}
P("J4", "Connector_Generic_MountingPin", "Conn_01x06_MountingPin", "Touch FPC 6P 0.5mm",
  "Connector_FFC-FPC:Hirose_FH12-6S-0.5SH_1x06-1MP_P0.50mm_Horizontal",
  dict(TP, MP="GND"), S, mpn="Hirose FH12-6S-0.5SH (check contact side of your CTP)")
R("R37", "10k", "TP_RST", "+3V3", S, lcsc=L_10K)
C("C52", "1uF", "+3V3", "GND", S, lcsc=L_1U)

SHEETS = [("power", "Pi header (5 V, GPIOs) and 3.3 V"),
          ("dsi", "Raspberry Pi DSI input, ICN6211 bridge"),
          ("panel", "AT070TN92 panel, bias supplies, VCOM, backlight, touch")]

# Only LCSC numbers that were verified are kept; everything else is matched by MPN/value.
_LCSC_OK = {L_100N, L_1U, L_10U0603, L_10K, L_4K7, L_1K, "C6186", "C15127", "C8545", L_100K, "C246085"}
for _p in PARTS:
    if _p.lcsc not in _LCSC_OK:
        _p.lcsc = ""


def nets():
    out = {}
    for p in PARTS:
        for pin, n in p.pins.items():
            if n is None:
                continue
            out.setdefault(n, []).append((p.ref, pin))
    return out


if __name__ == "__main__":
    ns = nets()
    for n in sorted(ns):
        if len(ns[n]) < 2:
            print("SINGLE-PIN NET:", n, ns[n])
    print(len(PARTS), "parts,", len(ns), "nets")
