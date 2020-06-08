---
# yaml_metadata_block with pandoc metadata
citekey-aliases:
  meta-review: https://greenelab.github.io/meta-review/v/6afcab41acf01822f8af8760184cd3cb2d67ab5f/
  tag:deep-review: doi:10.1098/rsif.2017.0387
  tag:paper-of-future: url:http://blogs.nature.com/naturejobs/2017/06/01/techblog-c-titus-brown-predicting-the-paper-of-the-future
references:
- type: personal_communication
  id: raw:dongbo-conversation
  title: Conversation with Dongbo Hu regarding how to administer a cloud server
  container-title: Greene Laboratory
  location: University of Pennsylvania
  issued: {'date-parts': [[2018, 12, 19]]}
manubot-requests-cache-path: .cache/requests-cache
manubot-log-level: INFO
...

# Testing markdown document for pandoc-manubot-cite filter

This is a sentence with one citation [@pmid:20170387].

This is a sentence with many citations [@pmid:20170387; @doi:10.7717/peerj.705].

```markdown
Citations in code blocks should not be modified [@pmid:20170387].
```

Defining citekeys with the link reference syntax [@issue; @bad-doi; @tag:bad-url].

[@issue]: url:https://github.com/manubot/manubot/pull/189
[@bad-doi]: doi:10.1016/S0022-2836(05)80360-2

[@tag:bad-url]: url:https://openreview.net/forum?id=HkwoSDPgg

Citing pre-defined citekey aliases [@meta-review; @tag:deep-review].

Citing @raw:dongbo-conversation whose metadata is already in pandoc's reference metadata.

Citing works whose reference metadata is provided via `--bibliography` [@arxiv:1407.3561; @tag:paper-of-future].

## References

::: {#refs}
:::
