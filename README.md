# Emilia


## Setting Up the Development Environment

This project uses Poetry for dependency management and [pre-commit](pyproject.toml#14%2C1-14%2C1) to ensure code quality standards. Follow these steps to set up your development environment:

### Prerequisites

- Ensure you have [Poetry installed](https://python-poetry.org/docs/#installation) on your system.
- Make sure Conda is installed as described in the previous sections for managing isolated environments.

### Initialize the Project

1. **Clone the Repository**: Start by cloning this repository to your local machine.

   ```bash
   git clone https://github.com/ArtisanLabs/Emilia
   cd Emilia
   ```

2. **Install Dependencies**: Use Poetry to install the project dependencies, including `pre-commit`.

   ```bash
   poetry install
   ```

   This command reads the `pyproject.toml` file and installs all necessary dependencies in an isolated environment.

3. **Activate the Conda Environment**: If you're using a Conda environment as described in the "Setting up Conda Environment" section, activate it:

   ```bash
   conda activate artisanlabs-emilia-backend
   ```

### Configure `pre-commit`

After installing the dependencies, set up `pre-commit` to run automatically before each commit:

1. **Install `pre-commit` Hooks**: With `pre-commit` already listed as a development dependency, install the Git hook scripts:

   ```bash
   poetry run pre-commit install
   ```

   This command sets up `pre-commit` to automatically run the configured hooks before each commit.

2. **Verify Installation**: Ensure that `pre-commit` is correctly installed and configured by running:

   ```bash
   poetry run pre-commit run --all-files
   ```

   This will run all configured hooks on all files, which is useful for initial setup and verification.

By following these steps, your development environment will be ready for working on the Emilia project. This setup ensures that you're using the correct versions of Python and project dependencies, while also adhering to code quality standards enforced by `pre-commit`.


## Development

To get started with the development environment for Emilia, you will need to use Conda, a popular package and environment management system. This allows you to create an isolated environment with specific versions of Python and other dependencies required for Emilia.

### Setting up Conda Environment

1. **Install Conda**: If you haven't already, download and install Conda from the [official website](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html). Make sure to choose the version that corresponds to your operating system.

2. **Create the Conda Environment**: Navigate to the backend directory of the Emilia project where the `environment.yml` file is located. Open a terminal in this directory and run the following command to create a new Conda environment named `artisanlabs-emilia-backend`:

   ```bash
   conda env create -f backend/environment.yml
   ```

   This command reads the `environment.yml` file and sets up an environment with Python 3.10 and all the necessary dependencies listed in the file.

3. **Activate the Environment**: Once the environment is successfully created, you can activate it by running:

   ```bash
   conda activate artisanlabs-emilia-backend
   ```

   Activating the environment will switch your terminal's context to use the Python version and dependencies specified for Emilia, isolating it from other projects.

4. **Verify the Environment**: To ensure everything is set up correctly, you can check the list of installed packages with:

   ```bash
   conda list
   ```

   This command will display all the packages installed in the active Conda environment, allowing you to verify that all necessary dependencies are in place.

5. **Deactivate the Environment**: When you're done working on Emilia, you can deactivate the Conda environment to return to your system's default Python settings by running:

   ```bash
   conda deactivate
   ```

By following these steps, you will have a dedicated development environment for working on Emilia, ensuring that all dependencies are correctly managed and isolated from other projects.
