from setuptools import setup, find_packages

setup(
    name="md2video",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'feedparser>=6.0.10',
        'beautifulsoup4>=4.12.2',
        'python-docx>=1.0.0',
        'requests>=2.31.0',
        'gTTS>=2.3.2',
        'moviepy>=1.0.3',
        'Pillow>=9.5.0',
        'python-frontmatter>=1.0.0',
        'python-dotenv>=1.0.0',
        'emoji'
    ],
    extras_require={
        'test': [
            'pytest>=7.4.4',
            'pytest-cov>=4.1.0',
            'pytest-mock>=3.12.0',
        ],
    },
    python_requires='>=3.9',
)
