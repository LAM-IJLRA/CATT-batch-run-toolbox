from setuptools import setup
setup(name="CATT_batch_processing",
		version=0.1,
		py_modules=["CATT_batch_processing"],
		install_requires=[
			"Click"
		],
		entry_points="""
			[console_scripts]
			autocatt=CATT_batch_processing:main
			"""
	 )
