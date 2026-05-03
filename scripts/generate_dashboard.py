from grafanalib._gen import write_dashboard
from grafanalib.core import Dashboard, Graph, Row, Target, YAxes, YAxis


def panel(title, expr):
    return Graph(
        title=title,
        dataSource="Prometheus",
        targets=[
            Target(
                expr=expr,
                legendFormat="{{ip}}",
            )
        ],
        yAxes=YAxes(
            left=YAxis(format="short"),
            right=YAxis(format="short"),
        ),
    )


def panel_chip_temp(title, expr):
    return Graph(
        title=title,
        dataSource="Prometheus",
        targets=[
            Target(
                expr=expr,
                legendFormat="{{ip}} chip",
            )
        ],
        yAxes=YAxes(
            left=YAxis(format="celsius"),
            right=YAxis(format="celsius"),
        ),
    )


def panel_pcb_temp(title, expr):
    return Graph(
        title=title,
        dataSource="Prometheus",
        targets=[
            Target(
                expr=expr,
                legendFormat="{{ip}} pcb",
            )
        ],
        yAxes=YAxes(
            left=YAxis(format="celsius"),
            right=YAxis(format="celsius"),
        ),
    )


dashboard = Dashboard(
    title="ASIC Monitoring",
    rows=[
        Row(
            panels=[
                panel("Hashrate (TH/s)", "asic_hashrate"),
            ]
        ),
        Row(
            panels=[
                panel("Temperature (°C)", "asic_temp"),
                panel_chip_temp("Chip Temp (°C)", "asic_chip_temp"),
                panel_pcb_temp("PCB Temp (°C)", "asic_pcb_temp"),
            ]
        ),
        Row(
            panels=[
                panel("Fan RPM", "asic_fan"),
                panel("Fan Duty (%)", "asic_fan_duty"),
            ]
        ),
        Row(
            panels=[
                panel("Power (W)", "asic_power_watts"),
                panel("Efficiency (J/TH)", "asic_efficiency"),
            ]
        ),
        Row(
            panels=[
                Graph(
                    title="Board Temps",
                    dataSource="Prometheus",
                    targets=[
                        Target(
                            expr="asic_board_temp",
                            legendFormat="{{ip}} board {{board}}",
                        )
                    ],
                )
            ]
        ),
    ],
).auto_panel_ids()

if __name__ == "__main__":
    with open("dashboard.json", "w", encoding="utf-8") as f:
        write_dashboard(dashboard, f)

    print("dashboard.json generated ✅")
