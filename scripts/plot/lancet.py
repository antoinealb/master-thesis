from collections import namedtuple
import re

Measurement = namedtuple('Measurement', [
    'target_rate',
    'rate',
    'latency_avg',
    'latency_percentiles',
    ])

def group_results(result_content):
    """
    Separates each result line, as well as options.

    Returns a tuple lancet_options, latency_groups, where latency_groups is a
    group of lines related to the same load.
    """
    result = result_content.splitlines()
    options, result = result[0], result[1:]

    groups = [result[i:i+5] for i in range(0, len(result), 6)]

    return options, groups


def parse_group(group):
    """
    Parses a measurement from a group of lines returned by group_results
    """
    target_rps = int(re.match("Load rate = (\d+)", group[0]).group(1))
    rate = float(group[2].split('\t')[1])
    latency_avg = int(group[4].split('\t')[0])

    percentiles = [50, 90, 95, 99]
    percentiles = dict(zip(percentiles, [float(s) for s in group[4].split('\t')[1:]]))

    return Measurement(target_rate=target_rps, rate=rate, latency_avg=latency_avg, latency_percentiles=percentiles)

def parse_results(content):
    _, groups = group_results(content)
    return [parse_group(g) for g in groups]
