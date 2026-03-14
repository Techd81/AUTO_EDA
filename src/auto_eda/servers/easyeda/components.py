"""STM32 minimum system board — pre-defined component library with LCSC part numbers.

All coordinates are in EDA internal units (0.01 inch).
Schematic range: approx -200 to 200 for A4 sheet.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Component:
    ref: str
    lcsc: str
    lcsc_alt: str
    value: str
    description: str
    lcsc_uuid: str = ""
    sch_x: int = 0
    sch_y: int = 0
    pcb_x: int = 0
    pcb_y: int = 0
    pcb_rotation: int = 0


LCSC_LIBRARY_UUID = "0819f05c4eef4c71ace90d822a990e87"

LCSC_DEVICE_UUIDS = {
    "C8734":   "accfc2f6010745268febab2459577079",
    "C6186":   "9f9c6cb41c7449fd8acf96aceed2661a",
    "C32346":  "ba37239063d74dbf872bace697d985f3",
    "C14663":  "96b39256cc3f4d80bd3b503deb4f3328",
    "C1560":   "4379d0d0956c42e8aea8af32d6588da5",
    "C19702":  "80646d555bcf4558bdde69f7f0e5dc8d",
    "C25744":  "c3b9baa5ef2e4070a4c0f9e9cd04fe6e",
    "C11702":  "65abbad5fa864933b552e0f016ece0db",
    "C92584":  "d24915886e8f45a3a48ccfd8b76b9361",
    "C165948": "74d31c19993b4b9581f3175a7da4b280",
    "C160935": "",
    "C124375": "413e1ee0270e47adab3cd56aebe55635",
    "C84256":  "65165b87e36a420bb0f83c56de791b8f",
}

STM32_MIN_SYS: list[Component] = [
    Component("U1",  "C8734",  "C74668",  "STM32F103C8T6",
              "ARM Cortex-M3 MCU LQFP-48",
              lcsc_uuid="accfc2f6010745268febab2459577079",
              sch_x=0,     sch_y=0,    pcb_x=25000, pcb_y=17500),
    Component("U2",  "C6186",  "C347289", "AMS1117-3.3",
              "LDO 3.3V 1A SOT-223",
              lcsc_uuid="9f9c6cb41c7449fd8acf96aceed2661a",
              sch_x=-600, sch_y=0,    pcb_x=5000,  pcb_y=17500),
    Component("Y1",  "C32346", "C388380", "8MHz",
              "8MHz crystal HC-49S SMD",
              lcsc_uuid="ba37239063d74dbf872bace697d985f3",
              sch_x=600,  sch_y=-300, pcb_x=30000, pcb_y=10000),
    Component("C1",  "C14663", "C1525",   "100nF",
              "100nF 0402 decoupling",
              lcsc_uuid="96b39256cc3f4d80bd3b503deb4f3328",
              sch_x=300,  sch_y=-500, pcb_x=23000, pcb_y=15000),
    Component("C2",  "C14663", "C1525",   "100nF",
              "100nF 0402 decoupling",
              lcsc_uuid="96b39256cc3f4d80bd3b503deb4f3328",
              sch_x=400,  sch_y=-500, pcb_x=24000, pcb_y=15000),
    Component("C3",  "C14663", "C1525",   "100nF",
              "100nF 0402 decoupling",
              lcsc_uuid="96b39256cc3f4d80bd3b503deb4f3328",
              sch_x=500,  sch_y=-500, pcb_x=25000, pcb_y=15000),
    Component("C4",  "C14663", "C1525",   "100nF",
              "100nF 0402 decoupling",
              lcsc_uuid="96b39256cc3f4d80bd3b503deb4f3328",
              sch_x=600,  sch_y=-500, pcb_x=26000, pcb_y=15000),
    Component("C5",  "C1560",  "C105620", "22pF",
              "22pF 0402 crystal load",
              lcsc_uuid="4379d0d0956c42e8aea8af32d6588da5",
              sch_x=500,  sch_y=-300, pcb_x=29000, pcb_y=10000),
    Component("C6",  "C1560",  "C105620", "22pF",
              "22pF 0402 crystal load",
              lcsc_uuid="4379d0d0956c42e8aea8af32d6588da5",
              sch_x=700,  sch_y=-300, pcb_x=31000, pcb_y=10000),
    Component("C7",  "C19702", "C77071",  "10uF",
              "10uF 0805 power filter",
              lcsc_uuid="80646d555bcf4558bdde69f7f0e5dc8d",
              sch_x=-700, sch_y=-300, pcb_x=4000,  pcb_y=15000),
    Component("C8",  "C14663", "C1525",   "100nF",
              "100nF 0402 LDO filter",
              lcsc_uuid="96b39256cc3f4d80bd3b503deb4f3328",
              sch_x=-500, sch_y=-300, pcb_x=6000,  pcb_y=15000),
    Component("R1",  "C25744", "C105573", "10k",
              "10k 0402 NRST pull-up",
              lcsc_uuid="c3b9baa5ef2e4070a4c0f9e9cd04fe6e",
              sch_x=700,  sch_y=300,  pcb_x=32000, pcb_y=20000),
    Component("R2",  "C25744", "C105573", "10k",
              "10k 0402 BOOT0 pull-down",
              lcsc_uuid="c3b9baa5ef2e4070a4c0f9e9cd04fe6e",
              sch_x=800,  sch_y=300,  pcb_x=33000, pcb_y=20000),
    Component("R3",  "C11702", "C182268", "1k",
              "1k 0402 LED current limit",
              lcsc_uuid="65abbad5fa864933b552e0f016ece0db",
              sch_x=-700, sch_y=300,  pcb_x=34000, pcb_y=25000),
    Component("SW1", "C92584", "C76766",  "RESET",
              "Reset tactile switch SMD",
              lcsc_uuid="d24915886e8f45a3a48ccfd8b76b9361",
              sch_x=500,  sch_y=300,  pcb_x=10000, pcb_y=25000),
    Component("J1",  "C165948","C165948", "USB-C",
              "USB Type-C connector",
              lcsc_uuid="74d31c19993b4b9581f3175a7da4b280",
              sch_x=-500, sch_y=500,  pcb_x=2000,  pcb_y=17500),
    Component("J2",  "C160935","C160935", "SWD",
              "SWD 4Pin debug header",
              lcsc_uuid="",
              sch_x=300,  sch_y=500,  pcb_x=45000, pcb_y=5000),
    Component("J3",  "C124375","C429962", "GPIO",
              "2x20 2.54mm pin header",
              lcsc_uuid="413e1ee0270e47adab3cd56aebe55635",
              sch_x=600,  sch_y=500,  pcb_x=20000, pcb_y=33000),
    Component("LED1","C84256", "C72038",  "PWR",
              "Red LED 0402 power indicator",
              lcsc_uuid="65165b87e36a420bb0f83c56de791b8f",
              sch_x=-700, sch_y=500,  pcb_x=35000, pcb_y=25000),
]

STM32_BY_REF: dict[str, Component] = {c.ref: c for c in STM32_MIN_SYS}
