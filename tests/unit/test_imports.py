def test_package_imports():
    import evidentia

    assert hasattr(evidentia, "__version__")
