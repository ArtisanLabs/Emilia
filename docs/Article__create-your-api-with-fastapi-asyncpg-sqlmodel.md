[

![Tomas Svojanovsky](https://archive.is/ZHcxN/581a954f7beb9be151ed54e8446800b9eee590f6.jpg)



](https://archive.is/o/ZHcxN/https://medium.com/@tomas.svojanovsky11)[

![Python in Plain English](https://archive.is/ZHcxN/5f41b284928b0815c88c117deb5edc9bda142b28.png)



](https://archive.is/o/ZHcxN/https://python.plainenglish.io/?source=post_page-----f3221a0063d6--------------------------------)

FastAPI is an incredibly powerful framework, known for its speed and efficiency in building robust web applications.

One of its key strengths lies in its seamless integration with databases, providing developers with a range of options. While using `SQLAlchemy` with `psycopg` is a popular choice, there’s another tool to unlock FastAPI’s full asynchronous potential — `asyncpg`.

![](https://archive.is/ZHcxN/7288dccea728ae9e657f142cd50af85b5709c1b2.webp)

## Supabase

We will use [Supabase](https://archive.is/o/ZHcxN/https://supabase.com/). You can set up your db with almost no effort. It can do much more, but we need just a db for our purposes.

Below are three steps we need to get started with the DB.

## Creating a database

Copy the password, we will need it later.

![](https://archive.is/ZHcxN/5cf78d78899c54fa3411624c9cb82e2512801b28.webp)

Supabase database setup

## Getting the credentials

From this page, you can get the credentials for the DB connection.

![](https://archive.is/ZHcxN/9c08f6450dfa6f43e1727f9e45489cc41ce35e77.webp)

Db credentials

That’s it. Good job! In a few steps, we have the database ready.

## Install dependencies

```
<span data-selectable-paragraph="" id="b476">pip install "fastapi[all]"<br>pip install asyncpg<br>pip install SQLAlchemy<br>pip install sqlmodel</span>
```

## Database connection setup

## settings.py

We will add our database credentials to a `.env` file, allowing for support across multiple environments. Most importantly, we do not want to expose our database credentials publicly. In the real-world app, the `.env` file is added to `.gitignore` and is not pushed to a remote repository.

```
<span data-selectable-paragraph="" id="27ed"><span>from</span> pydantic <span>import</span> BaseSettings<br><br><br><span>class</span> <span>Settings</span>(<span>BaseSettings</span>):<br>    DB_NAME: <span>str</span><br>    DB_PASSWORD: <span>str</span><br>    DB_USERNAME: <span>str</span><br>    DB_HOST: <span>str</span><br>    DB_PORT: <span>str</span><br><br>    <span>class</span> <span>Config</span>:<br>        env_file = <span>".env"</span></span>
```

## .env

Please use your Supabase credentials. I’ve included some here just as an example.

```
<span data-selectable-paragraph="" id="8f0e">DB_PASSWORD=3gIY4PcQ5V9CyO3E<br>DB_HOST=db.lntjnzlwpwpzaqzumext.supabase.co<br>DB_NAME=postgres<br>DB_USERNAME=postgres<br>DB_PORT=5432</span>
```

## database.py

We get our credentials from settings, add them to the URL to establish a database connection, and use the `init_db` function to create all tables based on the model.

While `drop_all` can be used during development to avoid complicated migrations, but it should be avoided in production because it has destructive results.

```
<span data-selectable-paragraph="" id="6953"><span>from</span> sqlmodel <span>import</span> SQLModel<br><br><span>from</span> sqlalchemy.ext.asyncio <span>import</span> AsyncSession, create_async_engine<br><span>from</span> sqlalchemy.orm <span>import</span> sessionmaker<br><br><span>from</span> settings <span>import</span> Settings<br><br>settings = Settings()<br><br>username = settings.DB_USERNAME<br>password = settings.DB_PASSWORD<br>dbname = settings.DB_NAME<br>db_port = settings.DB_PORT<br>db_host = settings.DB_HOST<br><br>SQLALCHEMY_DATABASE_URL = <span>f"postgresql+asyncpg://<span>{username}</span>:<span>{password}</span>@<span>{db_host}</span>:<span>{db_port}</span>/<span>{dbname}</span>"</span><br>engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=<span>True</span>)<br><br><br><span>async</span> <span>def</span> <span>init_db</span>():<br>    <span>async</span> <span>with</span> engine.begin() <span>as</span> conn:<br>        <span># await conn.run_sync(SQLModel.metadata.drop_all)</span><br>        <span>await</span> conn.run_sync(SQLModel.metadata.create_all)<br><br><br>async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=<span>False</span>, autocommit=<span>False</span>)</span>
```

## models.py

We define our database model here. You can fully utilize the `Field` from SQLModel, or if necessary, you can use `sa_column` from SQLAlchemy

```
<span data-selectable-paragraph="" id="413b"><span>from</span> datetime <span>import</span> datetime<br><span>from</span> sqlmodel <span>import</span> SQLModel, Field<br><span>import</span> sqlalchemy <span>as</span> sa<br><br><br><span>class</span> <span>User</span>(SQLModel, table=<span>True</span>):<br>    __tablename__ = <span>"users"</span><br><br>    user_id: <span>int</span> = Field(default=<span>None</span>, primary_key=<span>True</span>)<br>    username: <span>str</span> = Field(sa_column=sa.Column(sa.TEXT, nullable=<span>False</span>, unique=<span>True</span>))<br>    first_name: <span>str</span> = Field(sa_column=sa.Column(sa.TEXT, nullable=<span>False</span>))<br>    created_at: <span>str</span> = Field(sa_column=sa.Column(sa.DateTime(timezone=<span>True</span>), default=datetime.now))</span>
```

## Services

## user\_service.py

We created two methods: one for getting a user and another for creating a user. It’s worth noting that we user `UserCreateRequest`, which inherits from Pydantic. This allows us to ensure that we receive the data we expect.

```
<span data-selectable-paragraph="" id="c06e"><span>from</span> sqlmodel <span>import</span> Session, select<br><span>from</span> pydantic <span>import</span> BaseModel<br><span>from</span> models <span>import</span> User<br><br><br><span>class</span> <span>UserCreateRequest</span>(<span>BaseModel</span>):<br>    first_name: <span>str</span><br>    last_name: <span>str</span><br>    username: <span>str</span><br><br><br><span>class</span> <span>UserService</span>:<br>    <span>def</span> <span>__init__</span>(<span>self, session: Session</span>):<br>        self.session = session<br><br>    <span>async</span> <span>def</span> <span>create_user</span>(<span>self, data: UserCreateRequest</span>) -&gt; User:<br>        new_user = User(<br>            first_name=data.first_name,<br>            last_name=data.last_name,<br>            username=data.username,<br>        )<br><br>        self.session.add(new_user)<br>        <span>await</span> self.session.commit()<br><br>        <span>return</span> new_user<br><br>    <span>async</span> <span>def</span> <span>get</span>(<span>self, <span>id</span>: <span>int</span></span>) -&gt; User:<br>        query = (<br>            select(User)<br>            .where(User.user_id == <span>id</span>)<br>        )<br><br>        result = <span>await</span> self.session.execute(query)<br>        <span>return</span> result.scalars().one()</span>
```

## deps.py

This step is important because it enables us to leverage FastAPI’s dependency injection mechanism. We can define it like this and use it with the `UserService`.

Our service will have access to the database session, and at the same time, our controller can use the service without the need to create an instance of the service.

```
<span data-selectable-paragraph="" id="f022"><span>from</span> database <span>import</span> async_session<br><span>from</span> user_service <span>import</span> UserService<br><br><br><span>async</span> <span>def</span> <span>get_user_service</span>():<br>    <span>async</span> <span>with</span> async_session() <span>as</span> session:<br>        <span>async</span> <span>with</span> session.begin():<br>            <span>yield</span> UserService(session)</span>
```

## Controllers

## user\_controller.py

We can use `APIRouter` to isolate this logic from others. Within this router, we have two endpoints:

-   **\[POST\]** `/api/v1/users`
-   **\[GET\]** `/api/v1/users/{user_Id}`
-   If you’re curious about where we define `/api/v1`, we have to register it in the `main.py`. There you can define the prefix.

```
<span data-selectable-paragraph="" id="244a"><span>from</span> fastapi <span>import</span> APIRouter, Depends, Body<br><span>from</span> deps <span>import</span> get_user_service<br><span>from</span> models <span>import</span> User<br><span>from</span> user_service <span>import</span> UserService, CreateUserRequest<br><br>user_router = APIRouter(<br>    prefix=<span>"/users"</span>,<br>    tags=[<span>"Users"</span>]<br>)<br><br><br><span>@user_router.get(<span><span>"/{user_id}"</span>, response_model=User</span>)</span><br><span>async</span> <span>def</span> <span>get_user</span>(<span>*, user_service: UserService = Depends(<span>get_user_service</span>), user_id: <span>int</span></span>):<br>    <span>return</span> <span>await</span> user_service.get(user_id)<br><br><br><span>@user_router.post(<span><span>"/"</span>, response_model=User</span>)</span><br><span>async</span> <span>def</span> <span>create_user</span>(<span>*, user_service: UserService = Depends(<span>get_user_service</span>), user: CreateUserRequest = Body()</span>):<br>    <span>return</span> <span>await</span> user_service.create(user)</span>
```

## main.py

This is the starting point for our app. Here, we define the users’ router. The `on_startup` method will run at the beginning when we start our server (the next step). Its purpose is to create our tables in the database.

```
<span data-selectable-paragraph="" id="7652"><span>from</span> fastapi <span>import</span> FastAPI<br><br><span>from</span> database <span>import</span> init_db<br><span>from</span> user_controller <span>import</span> user_router<br><br>app = FastAPI(<br>    title=<span>"Asyncpg example"</span>,<br>    description=<span>"Create users with asyncpg"</span>,<br>    version=<span>"0.0.1"</span>,<br>)<br><br><br><span>@app.on_event(<span><span>"startup"</span></span>)</span><br><span>async</span> <span>def</span> <span>on_startup</span>():<br>    <span>await</span> init_db()<br><br><br><span>@app.get(<span><span>"/"</span></span>)</span><br><span>async</span> <span>def</span> <span>index</span>():<br>    <span>return</span> {<span>"message"</span>: <span>"Api is running"</span>}<br><br>app.include_router(user_router, prefix=<span>"/api/v1"</span>)</span>
```

## Run server

```
<span data-selectable-paragraph="" id="aca6">uvicorn main:app --reload</span>
```

## Command line

If everything runs correctly, you should see this in the command line. In the `database.py`, we defined `echo=True`, which will print out our SQL queries. It is good practice to check what's going on during development.

```
<span data-selectable-paragraph="" id="bf94">CREATE TABLE users (<br>        username TEXT NOT NULL,<br>        first_name TEXT NOT NULL,<br>        created_at TIMESTAMP WITH TIME ZONE,<br>        user_id SERIAL NOT NULL,<br>        PRIMARY KEY (user_id),<br>        UNIQUE (username)<br>)</span>
```

![](https://archive.is/ZHcxN/2d4187812331d91d1ab35cc47926b6a22266aa6a.webp)

User’s table in Supabase

## Testing

## Creating a user

![](https://archive.is/ZHcxN/23e6188ebf1a06572c63d54b5b8aab13ab3af064.webp)

## Getting a user by id

![](https://archive.is/ZHcxN/c756cd90ac9fd139e1570e11f25126180ce9b349.webp)

You can see the full code here: [Repository](https://archive.is/o/ZHcxN/https://github.com/redmonkez12/fastapi-asyncpg)