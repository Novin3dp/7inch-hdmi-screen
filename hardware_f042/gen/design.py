"""
Single source of truth for the AT070TN92 HDMI + USB-touch driver board, STM32F042F6P6 variant.

Everything (schematic, PCB netlist, BOM) is generated from the PARTS list below.
Pin numbers refer to the KiCad library symbol / footprint pad numbers.

Board function
  * HDMI in  -> LT8619C (HDMI RX -> 24-bit TTL RGB, DE mode) -> AT070TN92 50-pin FPC
  * Panel bias: TPS61040 boost (AVDD 10.4 V) + charge pumps (VGH +16 V, VGL -6.8 V)
                + LM321 VCOM buffer with trimmer (2.55 .. 4.5 V)
  * Backlight: TPS61165 constant-current boost, 182 mA, PWM dimming from the MCU
  * STM32F042F6P6 (TSSOP-20): configures LT8619C and reads GT915 touch over ONE shared I2C bus
    (LT8619C 0x32, GT915 0x5D) and presents a USB HID multi-touch digitizer to the Raspberry Pi
    (USB-C, also powers the board).  Differences to the STM32F072 board: one I2C bus, panel L/R and
    U/D scan direction set by resistors, no HDMI +5V sense input.
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
F_R0402 = "Resistor_SMD:R_0402_1005Metric"
F_R0603 = "Resistor_SMD:R_0603_1608Metric"
F_R0805 = "Resistor_SMD:R_0805_2012Metric"
F_C0402 = "Capacitor_SMD:C_0402_1005Metric"
F_C0603 = "Capacitor_SMD:C_0603_1608Metric"
F_C0805 = "Capacitor_SMD:C_0805_2012Metric"
F_C1206 = "Capacitor_SMD:C_1206_3216Metric"
F_FB0603 = "Inductor_SMD:L_0603_1608Metric"
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
L_5K1 = "C23186"
L_100K = "C25803"
L_22P = "C1555"

# =====================================================================
# Sheet 1: power input (USB-C) and regulators
# =====================================================================
S = "power"
P("J2", "Connector", "USB_C_Receptacle_USB2.0_16P", "USB-C (power + touch USB)",
  "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
  {"A1": "GND", "B1": "GND", "A12": "GND", "B12": "GND",
   "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
   "A5": "USB_CC1", "B5": "USB_CC2",
   "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM",
   "A8": NC, "B8": NC, "S1": "GND"}, S, mpn="HRO TYPE-C-31-M-12", lcsc="C165948")
R("R1", "5.1k", "USB_CC1", "GND", S, lcsc=L_5K1)
R("R2", "5.1k", "USB_CC2", "GND", S, lcsc=L_5K1)
P("F1", "Device", "Polyfuse_Small", "PTC 1.1A hold", "Fuse:Fuse_1206_3216Metric",
  {1: "VBUS", 2: "+5V"}, S, mpn="1206L110/16 (or BSMD1206-110)", lcsc="")
P("U4", "Power_Protection", "USBLC6-2SC6", "USBLC6-2SC6", F_SOT236,
  {1: "USB_DM", 6: "USB_DM", 3: "USB_DP", 4: "USB_DP", 2: "GND", 5: "+5V"}, S,
  mpn="USBLC6-2SC6", lcsc="C7519")
C("C1", "22uF", "+5V", "GND", S, fp=F_C0805, lcsc=L_22U0805)
C("C2", "100nF", "+5V", "GND", S, lcsc=L_100N)

P("U2", "Regulator_Linear", "AMS1117-3.3", "AMS1117-3.3", F_SOT223,
  {1: "GND", 2: "+3V3", 3: "+5V"}, S, mpn="AMS1117-3.3", lcsc="C6186")
C("C3", "22uF", "+3V3", "GND", S, fp=F_C0805, lcsc=L_22U0805)
C("C4", "100nF", "+3V3", "GND", S, lcsc=L_100N)
P("U3", "Regulator_Linear", "AMS1117-1.8", "AMS1117-1.8", F_SOT223,
  {1: "GND", 2: "+1V8", 3: "+5V"}, S, mpn="AMS1117-1.8", lcsc="C6187")
C("C5", "22uF", "+1V8", "GND", S, fp=F_C0805, lcsc=L_22U0805)
C("C6", "10uF", "+5V", "GND", S, fp=F_C0603, lcsc=L_10U0603)

# quiet analog rails for the LT8619C
P("FB1", "Device", "FerriteBead_Small", "600R@100MHz", F_FB0603, {1: "+1V8", 2: "+1V8A"}, S,
  mpn="BLM18PG601SN1D", lcsc="C1015")
C("C7", "10uF", "+1V8A", "GND", S, fp=F_C0603, lcsc=L_10U0603)
P("FB2", "Device", "FerriteBead_Small", "600R@100MHz", F_FB0603, {1: "+3V3", 2: "+3V3A"}, S,
  mpn="BLM18PG601SN1D", lcsc="C1015")
C("C8", "10uF", "+3V3A", "GND", S, fp=F_C0603, lcsc=L_10U0603)

for i, n in enumerate(["+5V", "+3V3", "+1V8", "AVDD", "VGH", "VGL", "VCOM", "GND"]):
    P("TP%d" % (i + 1), "Connector", "TestPoint", n, F_TP, {1: n}, S)

# =====================================================================
# Sheet 2: HDMI input and LT8619C
# =====================================================================
S = "hdmi"
P("J1", "Connector", "HDMI_A", "HDMI-A receptacle", "Connector_HDMI:HDMI_A_Amphenol_10029449-x01xLF_Horizontal",
  {1: "TMDS_D2_P", 2: "GND", 3: "TMDS_D2_N", 4: "TMDS_D1_P", 5: "GND", 6: "TMDS_D1_N",
   7: "TMDS_D0_P", 8: "GND", 9: "TMDS_D0_N", 10: "TMDS_CK_P", 11: "GND", 12: "TMDS_CK_N",
   13: NC, 14: NC, 15: "HDMI_SCL", 16: "HDMI_SDA", 17: "GND", 18: "HDMI_5V",
   19: "HDMI_HPD", "SH": "GND"}, S, mpn="Amphenol 10029449-001RLF (or equivalent SMT HDMI-A)")
R("R3", "1k", "LT_HPD", "HDMI_HPD", S, lcsc=L_1K)
R("R4", "100k", "HDMI_HPD", "GND", S, lcsc=L_100K)
R("R5", "47k", "HDMI_SCL", "HDMI_5V", S, lcsc="C25792")
R("R6", "47k", "HDMI_SDA", "HDMI_5V", S, lcsc="C25792")

LT = {
    1: "+1V8A", 2: "TMDS_CK_N", 3: "TMDS_CK_P", 4: "+3V3A", 5: "TMDS_D0_N", 6: "TMDS_D0_P",
    7: "+3V3A", 8: "TMDS_D1_N", 9: "TMDS_D1_P", 10: "+3V3A", 11: "TMDS_D2_N", 12: "TMDS_D2_P",
    13: "+1V8A", 14: NC, 15: NC, 16: "LT_REXT", 17: NC, 18: NC, 19: NC,
    20: "+3V3", 21: NC, 22: NC, 23: NC, 24: "LT_RSTN", 25: "+1V8", 26: NC, 27: NC,
    28: "LCD_B7", 29: "LCD_B6", 30: "LCD_B5", 31: "LCD_B4", 32: "LCD_B3", 33: "LCD_B2",
    34: "LCD_B1", 35: "LCD_B0", 36: "+3V3", 37: "LCD_G7", 38: "LCD_G6", 39: "LCD_G5",
    40: "LCD_G4", 41: "LCD_G3", 42: "LCD_G2", 43: "LCD_G1", 44: "LCD_G0", 45: "LCD_R7",
    46: "LCD_R6", 47: "LCD_R5", 48: "LCD_R4", 49: "LCD_R3", 50: "LCD_R2", 51: "LCD_R1",
    52: "LCD_R0", 53: "LCD_DE", 54: NC, 55: NC, 56: "LT_PCLK", 57: "+3V3", 58: "+1V8",
    59: "+1V8A", 60: "LT_XO", 61: "LT_XI", 62: "+3V3", 63: NC, 64: "+3V3", 65: "I2C_SDA",
    66: "I2C_SCL", 67: "+1V8", 68: NC, 69: NC, 70: NC, 71: NC, 72: NC, 73: NC,
    74: "LT_HPD", 75: "HDMI_SDA", 76: "HDMI_SCL", 77: "GND",
}
P("U1", "lcd_f042", "LT8619C", "LT8619C", "lcd_f042:Lontium_QFN-76_9x9mm_P0.4mm_EP5.81x6.31mm",
  LT, S, mpn="LT8619C (Lontium)", desc="HDMI1.4 receiver -> TTL RGB888")
R("R10", "2k 1%", "LT_REXT", "GND", S, lcsc="C4109")
R("R11", "22R", "LT_PCLK", "LCD_DCLK", S, lcsc="C25092")
R("R12", "10k", "LT_RSTN", "GND", S, lcsc=L_10K)
R("R13", "2.2k", "I2C_SDA", "+3V3", S, lcsc="C4190")   # shared bus LT8619C + GT915, 400 kHz
R("R14", "2.2k", "I2C_SCL", "+3V3", S, lcsc="C4190")
P("Y1", "Device", "Crystal_GND24", "25MHz 12pF", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
  {1: "LT_XI", 2: "GND", 3: "LT_XO", 4: "GND"}, S, mpn="X322525MOB4SI (25MHz CL=12pF)", lcsc="C9006")
C("C9", "18pF", "LT_XI", "GND", S, lcsc="C1549")
C("C10", "18pF", "LT_XO", "GND", S, lcsc="C1549")
# decoupling: one 100 nF per supply pin, placed at the pin
_dec = [("C11", "+1V8A", 1), ("C12", "+3V3A", 4), ("C13", "+3V3A", 7), ("C14", "+3V3A", 10),
        ("C15", "+1V8A", 13), ("C16", "+3V3", 20), ("C17", "+1V8", 25), ("C18", "+3V3", 36),
        ("C19", "+3V3", 57), ("C20", "+1V8", 58), ("C21", "+1V8A", 59), ("C22", "+3V3", 62),
        ("C23", "+3V3", 64), ("C24", "+1V8", 67)]
LT_DECAP = {}
for ref, net, pin in _dec:
    C(ref, "100nF", net, "GND", S, lcsc=L_100N)
    LT_DECAP[ref] = pin
C("C25", "10uF", "+1V8", "GND", S, fp=F_C0603, lcsc=L_10U0603)
C("C26", "10uF", "+3V3", "GND", S, fp=F_C0603, lcsc=L_10U0603)

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
  "lcd_f042:FPC_50P_P0.5_TopContact_AT070TN92", FPC, S,
  mpn="Hirose FH12A-50S-0.5SH(55) (top contact)",
  desc="pad numbers == panel FPC pin numbers")
R("R15", "10k", "LCD_MODE", "+3V3", S, lcsc=L_10K)     # DE mode
R("R16", "10k", "LCD_HS", "+3V3", S, lcsc=L_10K)       # HS/VS high in DE mode
R("R17", "10k", "LCD_VS", "+3V3", S, lcsc=L_10K)
R("R18", "10k", "LCD_DITHB", "+3V3", S, lcsc=L_10K)    # dithering off (24-bit input)
R("R19", "10k", "LCD_LR", "+3V3", S, lcsc=L_10K)       # left->right  (strap: move to GND to mirror)
R("R20", "10k", "LCD_UD", "GND", S, lcsc=L_10K)        # up->down     (strap: move to +3V3 to flip)
R("R21", "10k", "LCD_RST", "GND", S, lcsc=L_10K)       # panel held in reset until MCU
C("C27", "1uF", "+3V3", "GND", S, lcsc=L_1U)
C("C28", "100nF", "+3V3", "GND", S, lcsc=L_100N)

# --- bias supply, switched by MCU (BIAS_EN) for correct power sequencing
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
P("D3", "Device", "D_Zener", "16V 2%", F_SOD323, {1: "VGH", 2: "GND"}, S, mpn="BZX384-B16", lcsc="")
C("C35", "4.7uF 25V", "VGH", "GND", S, fp=F_C0805, lcsc="C1779")
# VGL: inverting charge pump, zener regulated to -6.8 V
C("C36", "100nF 50V", "AVDD_SW", "CP_N", S, fp=F_C0603, lcsc="C14663")
P("D4", "Diode", "BAT54S", "BAT54S", F_SOT23, {1: "VGL_RAW", 3: "CP_N", 2: "GND"}, S,
  mpn="BAT54S", lcsc="C19726")
C("C37", "1uF 25V", "VGL_RAW", "GND", S, fp=F_C0603, lcsc="C15849")
R("R27", "2.2k", "VGL_RAW", "VGL", S, lcsc="C25879")
P("D5", "Device", "D_Zener", "6.8V 2%", F_SOD323, {1: "GND", 2: "VGL"}, S, mpn="BZX384-B6V8", lcsc="")
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
R("R32", "100k", "BL_PWM", "GND", S, lcsc=L_100K)

# =====================================================================
# Sheet 4: MCU (STM32F042F6P6, TSSOP-20) + touch connector
# =====================================================================
S = "mcu"
# pin 1 = PB8/BOOT0 (BOOT0 function with the default option bytes), PA11/PA12 remapped onto pins 17/18
MCU = {1: "BOOT0", 2: "I2C_SDA", 3: "I2C_SCL", 4: "MCU_NRST", 5: "+3V3",
       6: "LT_RSTN", 7: "BIAS_EN", 8: "UART_TX", 9: "UART_RX", 10: "LCD_RST", 11: "LED_STAT",
       12: "BL_PWM", 13: "TP_RST", 14: "TP_INT", 15: "GND", 16: "+3V3",
       17: "USB_DM", 18: "USB_DP", 19: "SWDIO", 20: "SWCLK"}
P("U10", "MCU_ST_STM32F0", "STM32F042F6Px", "STM32F042F6P6", "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm",
  MCU, S, mpn="STM32F042F6P6", lcsc="C89040")
C("C45", "100nF", "+3V3", "GND", S, lcsc=L_100N)        # VDD  (pin 16)
C("C46", "100nF", "+3V3", "GND", S, lcsc=L_100N)        # VDDA (pin 5)
C("C47", "1uF", "+3V3", "GND", S, lcsc=L_1U)            # VDDA
C("C50", "4.7uF", "+3V3", "GND", S, fp=F_C0603, lcsc="C19666")
C("C51", "100nF", "MCU_NRST", "GND", S, lcsc=L_100N)
R("R33", "10k", "BOOT0", "GND", S, lcsc=L_10K)
P("SW1", "Switch", "SW_Push", "BOOT (DFU)", "Button_Switch_SMD:SW_SPST_B3U-1000P",
  {1: "BOOT0", 2: "+3V3"}, S, mpn="Omron B3U-1000P", lcsc="C231329")
P("D7", "Device", "LED", "green", F_LED0603, {1: "LED_K", 2: "LED_STAT"}, S, lcsc="C72043")
R("R34", "1k", "LED_K", "GND", S, lcsc=L_1K)
P("J5", "Connector_Generic", "Conn_01x07", "SWD/UART", "Connector_PinHeader_1.27mm:PinHeader_1x07_P1.27mm_Vertical",
  {1: "+3V3", 2: "SWCLK", 3: "SWDIO", 4: "MCU_NRST", 5: "UART_TX", 6: "UART_RX", 7: "GND"}, S, dnp=True)

# touch panel (GT915 on the touch-panel FPC, I2C)
TP = {1: "GND", 2: "+3V3", 3: "TP_INT", 4: "I2C_SCL", 5: "I2C_SDA", 6: "TP_RST"}
P("J4", "Connector_Generic_MountingPin", "Conn_01x06_MountingPin", "Touch FPC 6P 0.5mm",
  "Connector_FFC-FPC:Hirose_FH12-6S-0.5SH_1x06-1MP_P0.50mm_Horizontal",
  dict(TP, MP="GND"), S, mpn="Hirose FH12-6S-0.5SH (check contact side of your CTP)", lcsc="")
R("R37", "10k", "TP_RST", "+3V3", S, lcsc=L_10K)
C("C52", "1uF", "+3V3", "GND", S, lcsc=L_1U)

SHEETS = [("power", "Power input (USB-C) and regulators"),
          ("hdmi", "HDMI receiver LT8619C"),
          ("panel", "AT070TN92 panel, bias supplies, VCOM, backlight"),
          ("mcu", "STM32F042F6P6 controller and GT915 touch")]

# Only LCSC numbers that were verified are kept; everything else is matched by MPN/value.
_LCSC_OK = {L_100N, L_1U, L_10U0603, L_10K, L_4K7, L_1K, L_5K1, "C165948", "C7519", "C6186",
            "C15127", "C8545", L_100K}
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
