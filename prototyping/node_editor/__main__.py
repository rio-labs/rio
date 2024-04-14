from pathlib import Path

import rio

# Initialize the development component
HERE = Path(__file__).parent.resolve()

rio.DevelComponent.initialize(HERE)


app = rio.App(
    build=lambda: rio.DevelComponent(
        children=[
            rio.Column(
                rio.NodeInput("input 1", rio.Color.RED, key="input1"),
                rio.Text("Child 1"),
                rio.NodeOutput("output 1", rio.Color.RED, key="output1"),
            ),
            rio.NodeInput("input 2", rio.Color.RED, key="input2"),
            rio.NodeOutput("output 2", rio.Color.RED, key="output2"),
        ],
    ),
    theme=rio.Theme.from_color(light=False),
)

app.run_as_web_server(
    port=8001,
)
