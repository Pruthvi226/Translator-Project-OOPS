from evaluation.run import artifacts, score


def test_quality_metrics_on_known_fixture():
    # Exact-match fixture checks math only, not the quality of any model.
    reports = score([{'provider': 'fixture', 'source': 'Hello world', 'reference': 'Bonjour tout le monde.',
        'hypothesis': 'Bonjour tout le monde.', 'src_lang': 'en', 'target_lang': 'fr',
        'speech_reference': 'hello world', 'transcription': 'hello world',
        'ocr_reference': 'Hello', 'ocr_text': 'Hello', 'latency_ms': 100, 'run_elapsed_seconds': 0.2}])
    assert round(reports[0]['chrf'], 5) == 100
    assert reports[0]['wer'] == 0 and reports[0]['cer'] == 0
    assert reports[0]['requests_per_second'] == 5
    assert reports[0]['comet'] is None and reports[0]['estimated_cost_per_request_usd'] is None


def test_missing_measurements_not_invented():
    report = score([{'provider': 'unavailable', 'error': 'ProviderUnavailable'}])[0]
    assert report['bleu'] is None and report['p95_ms'] is None
    assert report['failure_rate'] == 1


def test_report_artifacts_export_measured_fields(tmp_path):
    # Verify export mechanics using an explicitly labelled fixture, not a model benchmark.
    reports = score([{'provider': 'fixture-only', 'source': 'Hello', 'reference': 'Bonjour',
                      'hypothesis': 'Bonjour', 'src_lang': 'en', 'target_lang': 'fr'}])
    artifacts(reports, tmp_path / 'reports')
    assert (tmp_path / 'reports' / 'quality.png').read_bytes().startswith(b'\x89PNG')
    text = (tmp_path / 'reports' / 'report.md').read_text(encoding='utf-8')
    assert 'fixture-only' in text and 'not measured' in text
