# Sources and attribution

This new tutorial is derived from Andreas Papaefstathiou's
[NewScalars repository](https://gitlab.com/apapaefs/NewScalars) at commit
`ae6fc19a71023d3ac9f26ce405b3de1eb89c20d6`.
The original repository remains the source for the earlier single-scalar,
MadSpin and Herwig/HwSim exercises. They are not required for the present
undecayed two-scalar project.

The model archive is copied unchanged from that repository:

```text
Model/loop_sm_scalar_180521_withaa_py3.tar.gz
SHA-256: f0531ad6e701d35cc55ba6c6799a07f1b99eb29f7bc8a029c663d4d8b144441f
```

Its UFO headers retain the original FeynRules/model information. For the manual
student installation, a second archive contains only the 24 `.py` source and
non-hidden `.dat` restriction files. Every included file is byte-for-byte
identical to the corresponding original. Historical bytecode, pickle caches,
hidden temporary cards and editor backups are omitted so students can simply
copy and extract the model themselves:

```text
Model/loop_sm_scalar_source.tar.gz
SHA-256: 2cc30d49391240d2a4f80bcea5d259b3ce9aa19d81ab4e36c1c2d662026aba8a
```

The optional instructor installer selects the same source files from the
original archive. Neither installation method modifies the physics source.

The analyser is a local adaptation of
[lheanalyzer](https://gitlab.com/apapaefs/lheanalyzer) at commit
`51150cde5f628d597b5a75fbb2a7e360f444fd39`.
See [the adaptation record](../lheanalyzer/UPSTREAM.md) for its original checksum
and the changes. The code is included directly, so a normal clone of this
tutorial needs no submodule initialization.

Students obtain MadGraph separately as the official
[3.5.16 release archive](https://launchpad.net/mg5amcnlo/3.0/3.5.x/+download/MG5_aMC_v3.5.16.tar.gz).
The original full event-generation test used the official
[3.5.16 Git tag](https://github.com/mg5amcnlo/mg5amcnlo/tree/v3.5.16), commit
`3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7`; see the [validation record](validation.md)
for what was checked with each distribution. Installations and generated process
code live under the ignored `Work/` directory, not in the tutorial history.
Retain the software/model citations printed in the MadGraph run banner when
using the calculation in scientific work.

The source snapshots of NewScalars and lheanalyzer contain no explicit project
licence. This repository preserves attribution and does not assign a replacement
licence to those sources. A licence for new material can be added by its owner.
