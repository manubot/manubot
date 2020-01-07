---
# yaml_metadata_block with pandoc metadata
citekey-aliases:
  tag:meta-review: url:https://greenelab.github.io/meta-review/
  tag:deep-review: doi:10.1098/rsif.2017.0387
  tag:paper-of-future: url:http://blogs.nature.com/naturejobs/2017/06/01/techblog-c-titus-brown-predicting-the-paper-of-the-future
references:
- type: personal_communication
  id: raw:dongbo-conversation
  title: Conversation with Dongbo Hu regarding how to administer a cloud server
  container-title: Greene Laboratory
  location: University of Pennsylvania
  issued: {'date-parts': [[2018, 12, 19]]}
manubot:
  requests-cache-path: .cache/requests-cache
...

# Testing markdown document for pandoc-manubot-cite filter

This is a sentence with one citation [@pmid:20170387].

This is a sentence with many citations [@pmid:20170387; @doi:10.7717/peerj.705].

```markdown
Citations in code blocks should not be modified [@pmid:20170387].
```

Defining citekeys with the link reference syntax [@tag:issue; @tag:bad-doi; @tag:bad-url].

[@tag:issue]: url:https://github.com/manubot/manubot/pull/189
[@tag:bad-doi]: doi:10.1016/S0022-2836(05)80360-2

[@tag:bad-url]: url:https://openreview.net/forum?id=HkwoSDPgg

Citing pre-defined citekey aliases [@tag:meta-review; @tag:deep-review].

Citing @raw:dongbo-conversation whose metadata is already in pandoc's reference metadata.

Citing works whose reference metadata is provided via `--bibliography` [@arxiv:1407.3561; @tag:paper-of-future].

## References

::: {#refs}
:::
