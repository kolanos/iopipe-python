import mock

from iopipe import IOpipeCore
from iopipe.contrib.trace import TracePlugin


@mock.patch("iopipe.report.send_report", autospec=True)
def test__trace_plugin(mock_send_report, handler_with_trace, mock_context):
    iopipe, handler = handler_with_trace

    assert len(iopipe.config["plugins"]) == 1

    handler({}, mock_context)

    assert len(iopipe.report.performance_entries) == 3
    assert any([e["name"] == "measure:foo" for e in iopipe.report.performance_entries])
    assert "@iopipe/plugin-trace" in iopipe.report.labels
    assert "@iopipe/metrics" not in iopipe.report.labels


@mock.patch("iopipe.report.send_report", autospec=True)
def test__trace_plugin_no_auto_measure(
    mock_send_report, handler_with_trace_no_auto_measure, mock_context
):
    iopipe, handler = handler_with_trace_no_auto_measure

    assert len(iopipe.config["plugins"]) == 1

    handler({}, mock_context)

    assert len(iopipe.report.performance_entries) == 2
    assert not any(
        [e["name"] == "measure:foo" for e in iopipe.report.performance_entries]
    )


@mock.patch("iopipe.report.send_report", autospec=True)
def test__trace_plugin__valid_schema(
    mock_send_report, handler_with_trace, mock_context, assert_valid_schema
):
    iopipe, handler = handler_with_trace

    handler({}, mock_context)

    assert_valid_schema(
        iopipe.report.report,
        optional_fields=[
            "clientId",
            "dbTraceEntries",
            "environment.nodejs",
            "environment.runtime.vendor",
            "environment.runtime.vmVendor",
            "environment.runtime.vmVersion",
            "errors.count",
            "errors.message",
            "errors.name",
            "errors.stack",
            "errors.stackHash",
            "eventType",
            "httpTraceEntries",
            "labels",
            "memory",
            "plugins.uploads",
            "projectId",
        ],
    )


@mock.patch("iopipe.report.send_report", autospec=True)
def test__trace_plugin__auto_http__http(
    mock_send_report, handler_with_trace_auto_http, mock_context
):
    iopipe, handler = handler_with_trace_auto_http

    assert len(iopipe.config["plugins"]) == 1

    handler({}, mock_context)

    assert len(iopipe.report.performance_entries) == 0

    http_traces = iopipe.report.http_trace_entries

    # There are two http traces because of the http -> https redirect
    assert len(http_traces) == 2

    for trace in http_traces:
        for key in ["name", "startTime", "duration", "type", "timestamp"]:
            assert key in trace

        for key in [
            "hash",
            "headers",
            "hostname",
            "method",
            "path",
            "pathname",
            "port",
            "protocol",
            "query",
            "url",
        ]:
            assert key in trace["request"]

        for header in trace["request"]["headers"]:
            assert "key" in header
            assert "string" in header

        for key in ["headers", "statusCode", "statusMessage"]:
            assert key in trace["response"]

        for header in trace["response"]["headers"]:
            assert "key" in header
            assert "string" in header


@mock.patch("iopipe.report.send_report", autospec=True)
def test_trace_plugin__auto_http__https(
    mock_send_report, handler_with_trace_auto_https, mock_context
):
    iopipe, handler = handler_with_trace_auto_https

    assert len(iopipe.config["plugins"]) == 1

    handler({}, mock_context)

    assert len(iopipe.report.performance_entries) == 0

    http_traces = iopipe.report.http_trace_entries

    assert len(http_traces) == 1

    for trace in http_traces:
        for key in ["name", "startTime", "duration", "type", "timestamp"]:
            assert key in trace

        for key in [
            "hash",
            "headers",
            "hostname",
            "method",
            "path",
            "pathname",
            "port",
            "protocol",
            "query",
            "url",
        ]:
            assert key in trace["request"]

        for header in trace["request"]["headers"]:
            assert "key" in header
            assert "string" in header

        for key in ["headers", "statusCode", "statusMessage"]:
            assert key in trace["response"]

        for header in trace["response"]["headers"]:
            assert "key" in header
            assert "string" in header


@mock.patch("iopipe.report.send_report", autospec=True)
def test_trace_plugin__auto_http__filter(
    mock_send_report, handler_with_trace_auto_http_filter, mock_context
):
    iopipe, handler = handler_with_trace_auto_http_filter

    handler({}, mock_context)

    assert len(iopipe.report.http_trace_entries) == 0


@mock.patch("iopipe.report.send_report", autospec=True)
def test_trace_plugin__auto_http__filter_request(
    mock_send_report, handler_with_trace_auto_http_filter_request, mock_context
):
    iopipe, handler = handler_with_trace_auto_http_filter_request

    handler({}, mock_context)

    traces = iopipe.report.http_trace_entries

    assert len(traces) == 1
    assert "request" not in traces[0]
    assert "response" in traces[0]


def test__trace_plugin__auto_http__env_var(monkeypatch):
    monkeypatch.setenv("IOPIPE_TRACE_AUTO_HTTP_ENABLED", "false")

    iopipe = IOpipeCore(plugins=[TracePlugin()])

    assert iopipe.plugins[0].auto_http is False
