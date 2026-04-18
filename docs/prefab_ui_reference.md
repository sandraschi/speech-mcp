# prefab_ui Reference (0.19.x)

Source-verified against the installed package in speech-mcp's venv. All imports and
signatures below are exact — checked directly from the `.py` files.

---

## Installation

```bash
# Comes with fastmcp[apps]:
uv add "fastmcp[apps]"

# Or standalone:
uv add prefab-ui
```

**Pin the version in production.** FastMCP sets only a minimum version; breaking changes
ship frequently.

---

## The pattern

```python
from prefab_ui.app import PrefabApp
from prefab_ui.components import Column, Heading, Text
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool(app=True)
def my_dashboard() -> PrefabApp:
    """Description shown to the model."""
    with Column(gap=4, css_class="p-6") as view:
        Heading("Title")
        Text("Body")
    return PrefabApp(title="My Dashboard", view=view)
```

`app=True` wires the Prefab renderer resource automatically. Return either a
`PrefabApp` (needed when you want a title or initial state) or a bare component
for simple stateless views.

---

## Import map

```python
# All layout/display/input components:
from prefab_ui.components import (
    # Layout
    Column, Row, Grid, GridItem, Container, Div, Separator, Slot,
    # Dashboard (explicit grid placement)
    Dashboard, DashboardItem,
    # Typography
    Heading,        # level=1..4
    Text,           # body text; accepts mixed Span/Link children
    H1, H2, H3, H4, P, Lead, Large, Small, Muted, BlockQuote,
    Markdown, Code, Kbd,
    # Status / labels
    Badge, Dot, Icon,
    # Data display
    Metric, DataTable, DataTableColumn, ExpandableRow,
    Table, TableHead, TableBody, TableRow, TableHeader, TableCell,
    TableFooter, TableCaption,
    # Media
    Image, Audio, Video, Embed, Svg,
    # Charts (inline histogram, not the charts submodule)
    Histogram, Ring, Progress, Sparkline,   # NOTE: Sparkline is in charts submodule
    # Inputs
    Input, Textarea, Checkbox, Switch, Slider, Select, SelectOption,
    SelectGroup, SelectLabel, SelectSeparator,
    Combobox, ComboboxOption, ComboboxGroup, ComboboxLabel, ComboboxSeparator,
    Radio, RadioGroup, DatePicker, Calendar, DropZone,
    # Buttons
    Button, ButtonGroup,
    # Forms
    Form, Field, FieldContent, FieldTitle, FieldDescription, FieldError, ChoiceCard,
    # Containers / overlays
    Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
    Accordion, AccordionItem, Dialog, Popover, HoverCard, Tooltip,
    Tabs, Tab, Pages, Page, Carousel,
    # Feedback
    Alert, AlertTitle, AlertDescription, Loader,
    # Charts (HTML-only, not chart library)
    Mermaid,
    # Control flow
    If, Elif, Else, ForEach,
    # Reactive system
    Rx, RxStr, STATE, ITEM, INDEX, EVENT, RESULT, ERROR,
    # Low-level
    Component, ContainerComponent, StatefulMixin, defer, insert,
    Link, Span,
)

# Charts submodule (Recharts-based):
from prefab_ui.components.charts import (
    BarChart, LineChart, AreaChart, PieChart,
    ScatterChart, RadarChart, RadialChart,
    Sparkline, ChartSeries,
)

# Control flow (also re-exported from prefab_ui.components):
from prefab_ui.components.control_flow import If, Elif, Else, ForEach

# Actions:
from prefab_ui.actions import (
    SetState, ToggleState, AppendState, PopState,   # state
    ShowToast, CloseOverlay,                         # UI feedback
    OpenLink,                                        # navigation
    Fetch,                                           # HTTP
    FileUpload, OpenFilePicker,                      # file
    SetInterval,                                     # timing
    CallHandler,                                     # custom
)
from prefab_ui.actions.mcp import CallTool, SendMessage   # MCP-specific

# Reactive:
from prefab_ui.rx import Rx, RxStr, STATE, ITEM, INDEX, EVENT, RESULT, ERROR

# App container:
from prefab_ui.app import PrefabApp

# FastMCPApp (for multi-tool apps with visibility control):
from fastmcp import FastMCPApp
```

---

## Components

### Layout

#### `Column(gap?, align?, justify?, css_class?)`
Vertical flex container. Use as context manager.

```python
with Column(gap=4, css_class="p-6") as view:
    Heading("Title")
    Text("Body")
```

- `gap`: Tailwind spacing int (2, 4, 6, 8…)
- `align`: `"start" | "center" | "end" | "stretch" | "baseline"`
- `justify`: `"start" | "center" | "end" | "between" | "around" | "evenly" | "stretch"`

#### `Row(gap?, align?, justify?, css_class?)`
Horizontal flex container. Same args as `Column`. Children size to content.
For equal-width columns use `Grid`.

```python
with Row(gap=2, align="center", justify="between"):
    Text("Label")
    Badge("Active", variant="success")
```

#### `Grid(columns?, gap?, css_class?)`
Auto-flow grid. Equal-width columns.

```python
with Grid(columns=3, gap=4):
    Metric(label="A", value=1)
    Metric(label="B", value=2)
    Metric(label="C", value=3)
```

#### `Dashboard(columns?, row_height?, rows?, gap?)` + `DashboardItem(col, row, col_span?, row_span?, z_index?)`
Explicit CSS Grid placement. Positions are **1-indexed**.

```python
with Dashboard(columns=12, row_height=120, gap=4):
    with DashboardItem(col=1, row=1, col_span=8, row_span=3):
        LineChart(...)
    with DashboardItem(col=9, row=1, col_span=4, row_span=1):
        Metric(label="Revenue", value="$42M")
```

#### `Separator(orientation?, spacing?)`
```python
Separator()                         # horizontal
Separator(orientation="vertical")
Separator(spacing=4)                # adds my-4 margin
```

---

### Typography

#### `Heading(content, level?)`
```python
Heading("Dashboard")              # h1
Heading("Details", level=2)       # h2
Heading("{{ section }}", level=3) # reactive
```
`level`: `1 | 2 | 3 | 4`

#### `Text(*args)`
```python
Text("Hello {{ name }}!")
Text("Click ", Span("here", bold=True), " to continue")   # rich text
```
Args: `bold`, `italic`, `underline`, `strikethrough`, `uppercase`, `lowercase`, `code`, `align`

#### Typography aliases
`H1`, `H2`, `H3`, `H4`, `P`, `Lead`, `Large`, `Small`, `Muted`, `BlockQuote` — all
accept `content` as first positional arg.

---

### Data Display

#### `Metric(label, value, delta?, trend?, trend_sentiment?, description?)`
KPI card.

```python
Metric(label="Revenue", value="$42M")
Metric(label="Users", value=1842, delta="+23.4%", trend="up")
Metric(label="Costs", value="$1.2M", delta="-15%", trend="down", trend_sentiment="positive")
```

- `trend`: `"up" | "down" | "neutral"` — inferred from delta sign if omitted
- `trend_sentiment`: `"positive" | "negative" | "neutral"` — controls colour; inferred from trend if omitted

#### `Badge(label, variant?)`
```python
Badge("Active")
Badge("Error", variant="destructive")
Badge("Draft", variant="secondary")
```
Variants: `"default" | "secondary" | "destructive" | "success" | "warning" | "info" | "outline" | "ghost"`

#### `DataTable(data, columns, expandable_rows?)`
```python
DataTable(
    data=[{"name": "Alice", "score": 98}],
    columns=[
        DataTableColumn(key="name", header="Name"),
        DataTableColumn(key="score", header="Score"),
    ],
)
```

---

### Buttons & Actions

#### `Button(label, variant?, size?, on_click?, disabled?, icon?)`
```python
Button("Save")
Button("Delete", variant="destructive")
Button("Cancel", variant="outline", size="sm")
Button("Refresh", on_click=CallTool("reload_data"))
Button("Toggle", on_click=ToggleState("showPanel"))
```

Variants: `"default" | "destructive" | "outline" | "secondary" | "ghost" | "link" | "success" | "warning" | "info"`
Sizes: `"default" | "xs" | "sm" | "lg" | "icon" | "icon-xs" | "icon-sm" | "icon-lg"`

---

### Charts (Recharts-based)

Import from `prefab_ui.components.charts`.

#### `ChartSeries(data_key, label?, color?)`
Defines one series. `data_key` is the field name in your data rows.

#### `BarChart(data, series, x_axis?, height?, stacked?, horizontal?, ...)`
```python
from prefab_ui.components.charts import BarChart, ChartSeries

BarChart(
    data=[
        {"month": "Jan", "desktop": 186, "mobile": 80},
        {"month": "Feb", "desktop": 305, "mobile": 200},
    ],
    series=[
        ChartSeries(data_key="desktop", label="Desktop"),
        ChartSeries(data_key="mobile", label="Mobile"),
    ],
    x_axis="month",
    stacked=True,
    height=300,
)
```

#### `LineChart(data, series, x_axis?, curve?, show_dots?, height?, ...)`
`curve`: `"linear" | "smooth" | "step"`

#### `AreaChart(data, series, x_axis?, stacked?, curve?, height?, ...)`

#### `PieChart(data, data_key, name_key, inner_radius?, show_label?, height?, ...)`
`inner_radius > 0` = donut chart.

```python
PieChart(
    data=[{"browser": "Chrome", "visitors": 275}, {"browser": "Safari", "visitors": 200}],
    data_key="visitors",
    name_key="browser",
    inner_radius=60,
)
```

#### `ScatterChart(data, series, x_axis, y_axis, z_axis?, height?, ...)`

#### `RadarChart(data, series, axis_key?, filled?, height?, ...)`

#### `RadialChart(data, data_key, name_key, inner_radius?, start_angle?, end_angle?, height?, ...)`

#### `Sparkline(data, variant?, fill?, curve?, mode?, stroke_width?, height?)`
Inline micro-chart. Takes a flat list of numbers.

```python
from prefab_ui.components.charts import Sparkline

Sparkline(data=[10, 15, 8, 22, 18, 25])
Sparkline(data=[10, 15, 8, 22], variant="success", fill=True)
Sparkline(data=[5, 12, 8, 3], curve="smooth", css_class="w-24")
```
Variants: `"default" | "success" | "warning" | "destructive" | "info" | "muted"`
Modes: `"line" | "bar"`

---

### Forms & Inputs

#### `Form(on_submit?)`
```python
from prefab_ui.actions.mcp import CallTool
from prefab_ui.actions import SetState, ShowToast
from prefab_ui.rx import RESULT

with Form(on_submit=CallTool("save", on_success=[SetState("items", RESULT), ShowToast("Saved!", variant="success")])):
    Input(name="title", label="Title", required=True)
    Button("Submit", button_type="submit")
```

#### `Input(name, label?, placeholder?, required?, on_change?)`
#### `Textarea(name, label?, placeholder?, required?)`
#### `Checkbox(name, label?)`
#### `Switch(name, label?)`
#### `Slider(name, min, max, step?, label?)`
#### `Select(name, label?, options?)` + `SelectOption(value, label)`
#### `Radio(value, label)` / `RadioGroup(name, label?)`
#### `DatePicker(name, label?)`

---

### Actions

```python
from prefab_ui.actions import SetState, ToggleState, AppendState, PopState
from prefab_ui.actions import ShowToast, CloseOverlay, OpenLink
from prefab_ui.actions import Fetch, SetInterval
from prefab_ui.actions.mcp import CallTool, SendMessage
```

#### State
```python
SetState("key", value)           # set state key to value
SetState("key")                  # set key to $event (use in on_change)
ToggleState("boolKey")
AppendState("listKey", item)
PopState("listKey")
```

#### MCP
```python
CallTool("tool_name", arguments={"param": "{{ stateKey }}"})
CallTool("tool_name", on_success=SetState("results", RESULT))
SendMessage("Summarize this")    # sends message to the model
```

#### UI
```python
ShowToast("Saved!", variant="success")   # variants: default, success, destructive, warning
CloseOverlay()
OpenLink("https://example.com", new_tab=True)
```

#### Composing actions (list = sequential)
```python
Button("Submit", on_click=[
    SetState("loading", True),
    CallTool("process", arguments={"q": "{{ query }}"}),
    ShowToast("Done!"),
])
```

---

### Reactive state (`Rx`)

```python
from prefab_ui.rx import Rx, STATE, ITEM, INDEX, EVENT, RESULT, ERROR

# Named state reference
count = Rx("count")
count + 1              # {{ count + 1 }}
count > 0              # {{ count > 0 }}
(count > 0).then("yes", "no")   # ternary

# STATE proxy (equivalent to Rx("key"))
STATE.revenue          # Rx("revenue")
STATE.user.name        # Rx("user.name")

# Pipes
Rx("revenue").currency()           # {{ revenue | currency }}
Rx("name").upper().truncate(20)    # {{ name | upper | truncate:20 }}
Rx("price").compact()              # {{ price | compact }}  → "42K"

# In components
Metric(label="Count", value=count)
Text(f"Hello {STATE.username}!")

# Loop variables
with ForEach("items") as item:
    Text(item.name)           # {{ $item.name }}

with ForEach("items") as (i, item):   # enumerate style
    Text(f"{i + 1}. {item.name}")

# Built-in reactive vars
# EVENT  — value from on_change
# RESULT — result from CallTool on_success
# ERROR  — error message in on_error
# ITEM   — current ForEach item
# INDEX  — current ForEach index
```

---

### Control Flow

```python
from prefab_ui.components import If, Elif, Else, ForEach
# (also importable from prefab_ui.components.control_flow)

with If(STATE.show):
    Text("Visible")
with Else():
    Text("Hidden")

with ForEach("items") as item:
    Text(item.title)
```

---

## `PrefabApp`

```python
PrefabApp(
    view=view,           # required: root component
    title="My App",      # optional: sets page title
    state={"key": val},  # optional: initial client-side state
)
```

Return a bare component instead of `PrefabApp` for simple stateless views.

---

## `FastMCPApp` (multi-tool apps)

Use when you need tool visibility control (`app`-only tools hidden from the model):

```python
from fastmcp import FastMCPApp
from prefab_ui.server.apps import AppConfig   # for visibility

app = FastMCPApp("MyApp")

@app.ui()                          # entry point — model can see this
def open_dashboard() -> PrefabApp:
    ...

@app.tool(app=AppConfig(visibility=["app"]))   # UI-only — hidden from model
def search(q: str) -> PrefabApp:
    ...
```

---

## Gotchas

- `Heading("text", level=3)` — `level` is keyword-only when using positional `content`
- `Button` and `Badge` accept label as first positional arg
- `ChartSeries(data_key=...)` — `data_key` is the Python name; serialises to `dataKey` (alias)
- `Dashboard` + `DashboardItem` positions are **1-indexed** (CSS Grid convention)
- `Sparkline` is in `prefab_ui.components.charts`, not `prefab_ui.components`
- `Rx` objects are immutable; all operators return new `Rx` instances
- `ForEach("items")` references a state key by name (string), not an Rx object
- Actions in `on_click` / `on_change` / `on_submit` accept a single action or a list
- `button_type="button"` prevents form submission for cancel/close buttons inside `Form`
- `prefab_ui` breaks frequently — pin version in production (`prefab-ui==0.19.1`)
