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

## References

::: {#refs}
:::
