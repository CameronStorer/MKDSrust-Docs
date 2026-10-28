# Accuracy and native modes
<!-- Modders -->

Here **Accuracy mode** means the established exact hardware baseline. It preserves the project's cycle-counted hardware behavior for regression checks; the cited launcher does not document a button with that label. It is not a claim of universal accuracy against a physical DS.

## Select a runtime mode
The hardware switches accept exact or native. Leave experiments off for ordinary baseline play. To select an explicit exact baseline in PowerShell before starting the game:
~~~powershell
$env:MKDS_HW_FS = 'exact'
$env:MKDS_HW_ARM7 = 'exact'
$env:MKDS_HW_TIME = 'exact'
$env:MKDS_HW_SND = 'exact'
.\play.bat --stats
~~~
Change one value to native to test its replacement. Use Remove-Item Env:MKDS_HW_FS (and the other variable names) to remove overrides afterwards. These changes apply to the current terminal and its children. The graphical launcher's three Advanced toggles affect only the child game process and remove inherited overrides when off; it has no SND or timing toggle in the reviewed version.

| Switch | Native behavior |
|---|---|
| MKDS_HW_FS | Read game files directly from the in-memory ROM |
| MKDS_HW_ARM7 | Answer secondary-processor service messages through a native router |
| MKDS_HW_TIME | Virtual OS time and interrupts at safe points |
| MKDS_HW_SND | Boot and run the translated sound/interrupt work as event-driven plain calls; zero ARM7 CPU cycles in the latest report |

MKDS_TIMING=native is a **build-time** option, or generator --timing native; setting it only when playing does not regenerate an exact build. It removes most instruction-budget bookkeeping. Native timing is opt-in. See [hardware replacement](hardware.md) for limits.

MKDS_NATIVES=all enables trial native function replacements; off selects translations. Only ten verified helpers are normally installed. This switch is distinct from hardware service switches. MKDS_FLAT=1 selects flat dispatch instead of default fibers; MKDS_T1=off/all/<file> helps bisect raised code; MKDS_EXACT=1 disables dead-flag elimination. These are developer diagnostics.

Sources: [launcher](../sources/launcher.md), [dictionary](../sources/dictionary.md), [Block 4](../sources/BLOCK4_SOURCE_PLAN.md), [latest defaults proposal](../sources/BLOCK5_DEFAULTS.md). [Verify changes](verify.md).
