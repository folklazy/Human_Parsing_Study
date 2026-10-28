# Human Parsing Benchmark — current status

Updated:2026-10-28T04:40:10.984117+00:00 UTC

**CIHP_NATIVE_FIRST_SIX_VALIDATION_RUNNING** — user-authorized full official nativeCIHP5000×6batch started. No subset substitution, noSapiens/Ninja/color/training/CCTV. [PLAN](PLAN.md),[authority](proposals/CIHP_NATIVE_PARSING9_CODEX_PLAN_TH_20261028.md),[readiness](reports/CIHP_NATIVE_READINESS.md). HistoricalYOLO/CPIresultsunchanged.

RunID`cihp-native-six-20261028T034103254470Z`. Actual launch codecommit`5e8f36ae2a249295c6a1b424b066b010449da048`,configSHA`3b6c98ef8056bc24c0a503559972619b7cb82bcf40cdfa2983579a84567c5a24`. Externalroot`Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z`. ControllerPID34503;permodelPIDs/commandsandcurrentstateinLAUNCH.json,permodelRUN.json/FRAMES.jsonl/logsundervalidation/. Currentmodelcountsarehealth/completenessonly,notpartialranking.Modelscopeorderfixedinconfig;oneGPUworkeratonce.

Terminal-only reporter scripts/report_cihp_batch.py writesSUMMARY/PER_CLASS/PERSON_METRICS/FAILURES/NATIVE_REFERENCE andrun-specificcompletionreport. Monitor scripts/monitor_cihp_batch.py logsGPUhealthandinvokesreporteronlyafterbatchterminal;itcannotstart/retryinference. Terminalreportsareautocommitted/pushedonlyifpublicationcheckoutclean;otherwisePENDING_SYNC,preserveindependentwork. No GPUbenchmarkrerunfordocumentation.

Next:allowapprovedbatchtofinishunderstop/resourcepolicy,thenreviewactualterminalreport. STRICT_COMPLETE keepsnullmainmetricsforincompletesystems. No live-score tuning/newmodelselection;nativeconfidenceexportandinlineparser-timingscope limitsaredisclosed. If processinterruptionoccurs,inspectactualPIDs/artifactsbeforeanycontrolledcontinuation;noautomaticfailedinputretry.

Reporting continuation: original inference batch remains active. Read-only monitor uses a new health-log segment after documentation/source refresh; prior telemetry remains intact. Terminal reporting includes the fixed 16-image comparison index and updates this current-state document with the observed batch outcome. This is not an inference restart.
