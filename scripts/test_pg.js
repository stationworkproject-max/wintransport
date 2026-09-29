import pg from 'pg';
const { Client } = pg;

const configs = [
  {
    host: 'db.rqwpafatgsyncvretjym.supabase.co',
    port: 5432,
    user: 'postgres',
    password: '14150393Asas/',
    database: 'postgres',
    ssl: { rejectUnauthorized: false }
  },
  {
    host: 'aws-0-eu-central-1.pooler.supabase.com',
    port: 6543,
    user: 'postgres.rqwpafatgsyncvretjym',
    password: '14150393Asas/',
    database: 'postgres',
    ssl: { rejectUnauthorized: false }
  },
  {
    host: 'aws-0-eu-central-1.pooler.supabase.com',
    port: 5432,
    user: 'postgres.rqwpafatgsyncvretjym',
    password: '14150393Asas/',
    database: 'postgres',
    ssl: { rejectUnauthorized: false }
  }
];

async function test() {
  for (const cfg of configs) {
    console.log(`Connecting to ${cfg.host}:${cfg.port}...`);
    const client = new Client(cfg);
    try {
      await client.connect();
      console.log('SUCCESSFULLY CONNECTED TO DATABASE!');
      const res = await client.query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;");
      console.log('Tables:', res.rows.map(r => r.table_name));
      await client.end();
      return client;
    } catch (e) {
      console.log(`Failed ${cfg.host}:${cfg.port} - ${e.message}`);
    }
  }
}

test();
