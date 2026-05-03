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


dashboard = Dashboard(
    title="ASIC Monitoring",
    rows=[
        Row(
            panels=[
                panel("Hashrate (TH/s)", "asic_hashrate_ths"),
                panel("Temperature (°C)", "asic_temp_max"),
            ]
        ),
        Row(
            panels=[
                panel("Fan RPM", "asic_fan_avg"),
                panel("Power (W)", "asic_power_watts"),
            ]
        ),
        Row(
            panels=[
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
    # print(json.dumps(
    #     dashboard.to_json_data(),
    #     cls=DashboardEncoder,
    #     indent=2
    # ))
    with open("dashboard.json", "w", encoding="utf-8") as f:
        write_dashboard(dashboard, f)

    print("dashboard.json generated ✅")
