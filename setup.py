from setuptools import setup, find_packages
setup(name="autocatt",
		version=0.1,
		py_modules=["autocatt", "CATT_materialModifier"],
		install_requires=[
			"Click",
            "Kivy",
            "pathlib",
		],
		entry_points="""
			[console_scripts]
			acbatch=CATT_batch_processing:main
			acmaterials=CATT_materialModifier:main
			acresults=CATT_results_comparison:main
			""",
        packages = find_packages(),
        #package_dir={'.': 'autocatt'},
        include_package_data=True,
        package_data = {"": ["*.kv"]},
        data_files = [("autocatt/resources", ["autocatt/resources/materialsGUI.kv"])]
	 )
