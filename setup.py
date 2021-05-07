from setuptools import setup
setup(name="autocatt",
		version=0.1,
		py_modules=["autocatt"],
		install_requires=[
			"Click"
		],
		entry_points="""
			[console_scripts]
			acbatch=CATT_batch_processing:main
			acmaterials=CATT_materialModifier:main
			acresults=CATT_results_comparison:main
			"""
	 )
