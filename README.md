# DGCV

This is the datapack for **D**efinitive **G**alaci**c**raft **V**anilla.

To learn more about GCV visit the [wiki][wiki].

## Compiling

All functions in this datapack use the custom [ff][ff] tool to increase code
density and allow for constants to be easily shared accross functions.

To compile the `.ff` files into `.mcfunction` files (assuming a Windows system):

```
> cd data\gcv\functions
> py -3.10 ..\..\..\tools\ff.py
```

[wiki]: https://gcv.fandom.com/
[ff]: tools/ff.py
