const sequelize = require('../config/database');
const Conversation = require('../models/Conversation');
const SyncService = require('../services/syncService');
const { Op } = require('sequelize');

const ANA_AGENT_ID = process.env.AGENT_ID || 'agent_3501k1kf5424fdfa3746wxcsfh91';

// Configuración de fecha desde .env o código
const SYNC_START_DATE = process.env.SYNC_START_DATE || null; // Formato: 'YYYY-MM-DD' o 'YYYY-MM-DD HH:mm:ss'
const SYNC_END_DATE = process.env.SYNC_END_DATE || null; // Fecha límite superior opcional
const SYNC_LAST_DAYS = process.env.SYNC_LAST_DAYS || null; // Número de días hacia atrás

function getCallStartAfterUnix() {
  let callStartAfterUnix = null;

  if (SYNC_START_DATE) {
    const date = new Date(SYNC_START_DATE);
    if (!isNaN(date.getTime())) {
      callStartAfterUnix = Math.floor(date.getTime() / 1000);
      console.log(`📅 Usando fecha desde .env (inicio): ${date.toLocaleString()} (Unix: ${callStartAfterUnix})`);
    } else {
      console.warn(`⚠️  Fecha inválida en SYNC_START_DATE: ${SYNC_START_DATE}`);
    }
  } else if (SYNC_LAST_DAYS) {
    const days = parseInt(SYNC_LAST_DAYS, 10);
    if (!isNaN(days) && days > 0) {
      const date = new Date();
      date.setDate(date.getDate() - days);
      callStartAfterUnix = Math.floor(date.getTime() / 1000);
      console.log(`📅 Usando últimos ${days} días desde .env: ${date.toLocaleString()} (Unix: ${callStartAfterUnix})`);
    } else {
      console.warn(`⚠️  Valor inválido en SYNC_LAST_DAYS: ${SYNC_LAST_DAYS}`);
    }
  }

  return callStartAfterUnix;
}

function getCallEndBeforeUnix() {
  if (!SYNC_END_DATE) {
    return null;
  }

  const date = new Date(SYNC_END_DATE);
  if (isNaN(date.getTime())) {
    console.warn(`⚠️  Fecha inválida en SYNC_END_DATE: ${SYNC_END_DATE}`);
    return null;
  }

  const unix = Math.floor(date.getTime() / 1000);
  console.log(`📅 Usando fecha desde .env (fin): ${date.toLocaleString()} (Unix: ${unix})`);
  return unix;
}

async function syncAnaConversations(startDate = null, endDate = null) {
  try {
    console.log('🎯 === SINCRONIZACIÓN DE CONVERSACIONES DE ANA RODRIGUEZ ===');
    console.log(`📋 Agente ID: ${ANA_AGENT_ID}`);

    let callStartAfterUnix = null;
    let callEndBeforeUnix = null;

    // Prioridad: parámetro > .env > sin filtro
    if (startDate) {
      const date = new Date(startDate);
      if (!isNaN(date.getTime())) {
        callStartAfterUnix = Math.floor(date.getTime() / 1000);
        console.log(`📅 Usando fecha del parámetro: ${date.toLocaleString()} (Unix: ${callStartAfterUnix})`);
      } else {
        console.warn(`⚠️  Fecha inválida en parámetro: ${startDate}`);
      }
    } else {
      callStartAfterUnix = getCallStartAfterUnix();
    }

    callEndBeforeUnix = endDate
      ? parseEndDate(endDate)
      : getCallEndBeforeUnix();

    if (!callStartAfterUnix) {
      console.log(`📅 Sin filtro de fecha inicial - sincronizando desde el origen disponible`);
    }

    if (callEndBeforeUnix) {
      console.log(`📅 Sincronizando solo hasta ${new Date(callEndBeforeUnix * 1000).toLocaleString()}`);
    }

    console.log('='.repeat(70));

    await sequelize.authenticate();
    console.log('✅ Conexión a la base de datos establecida');

    await sequelize.sync({ alter: true });
    console.log('✅ Modelos sincronizados');

    const syncService = new SyncService();

    console.log('\n🔄 Iniciando sincronización...');
    const results = await syncService.syncAllConversations(ANA_AGENT_ID, callStartAfterUnix, callEndBeforeUnix);

    console.log('\n' + '='.repeat(70));
    console.log('📊 RESULTADOS DE SINCRONIZACIÓN');
    console.log('='.repeat(70));
    console.log(`🎯 Agente: Ana Rodriguez (${ANA_AGENT_ID})`);

    console.log('\n' + '='.repeat(70));
    console.log('📈 ESTADÍSTICAS DE BASE DE DATOS');
    console.log('='.repeat(70));

    const totalConversations = await Conversation.count({
      where: { agent_id: ANA_AGENT_ID }
    });

    const conversationsWithTranscript = await Conversation.count({
      where: {
        agent_id: ANA_AGENT_ID,
        transcript: { [Op.ne]: null }
      }
    });

    console.log(`💬 Total conversaciones de Ana en BD: ${totalConversations}`);
    console.log(`📝 Conversaciones con transcript: ${conversationsWithTranscript}`);

    console.log('\n' + '='.repeat(70));
    console.log('📋 CONVERSACIONES RECIENTES (últimas 5)');
    console.log('='.repeat(70));

    const recentWhere = { agent_id: ANA_AGENT_ID };
    if (callStartAfterUnix) {
      recentWhere.createdAt = { [Op.gte]: new Date(callStartAfterUnix * 1000) };
    }
    if (callEndBeforeUnix) {
      recentWhere.createdAt = {
        ...(recentWhere.createdAt || {}),
        [Op.lte]: new Date(callEndBeforeUnix * 1000)
      };
    }

    const recentConversations = await Conversation.findAll({
      where: recentWhere,

      limit: 5,
      attributes: ['conversation_id', 'status', 'transcript']
    });

    recentConversations.forEach((conv, index) => {
      console.log(`${index + 1}. 💬 ${conv.conversation_id}`);
      console.log(`   📛 Nombre: ${conv.name || 'Sin nombre'}`);
      console.log(`   📊 Estado: ${conv.status}`);
      console.log(`   📝 Transcript: ${conv.transcript ? '✅' : '❌'}`);
      console.log('');
    });

    console.log('🎉 Sincronización completada exitosamente');

  } catch (error) {
    console.error('💥 Error en sincronización:', error.message);
    console.error(error.stack);
    process.exit(1);
  } finally {
    await sequelize.close();
    console.log('🔌 Conexión a la base de datos cerrada');
  }
}

function parseEndDate(dateString) {
  const date = new Date(dateString);
  if (isNaN(date.getTime())) {
    console.warn(`⚠️  Fecha inválida en parámetro endDate: ${dateString}`);
    return null;
  }
  return Math.floor(date.getTime() / 1000);
}

function parseStartDate(dateString) {
  const date = new Date(dateString);
  if (isNaN(date.getTime())) {
    console.warn(`⚠️  Fecha inválida en parámetro startDate: ${dateString}`);
    return null;
  }
  return Math.floor(date.getTime() / 1000);
}

if (require.main === module) {
  const [, , startArg, endArg] = process.argv;
  syncAnaConversations(startArg, endArg);
}

module.exports = syncAnaConversations;