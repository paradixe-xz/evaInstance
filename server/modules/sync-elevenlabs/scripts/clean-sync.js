const sequelize = require('../config/database');
const { Op } = require('sequelize'); // Agregar esta línea
const Conversation = require('../models/Conversation');
const SyncService = require('../services/syncService');
require('dotenv').config();

async function cleanAndSync() {
  try {
    await sequelize.authenticate();
    console.log('Conexión a base de datos establecida.');
    
    // Sincronizar modelos (esto actualizará la estructura de la tabla)
    await sequelize.sync({ alter: true });
    console.log('Modelos sincronizados con la base de datos.');
    
    // Opcional: limpiar conversaciones con errores
    console.log('\n¿Deseas limpiar conversaciones con errores? (Comentar la siguiente línea si no)');
    // await Conversation.destroy({ where: {} }); // Descomentar para limpiar todo
    
    const syncService = new SyncService();
    const results = await syncService.syncAllConversations();
    
    console.log('\n=== RESULTADOS DE SINCRONIZACIÓN ===');
    console.log(`Total de conversaciones: ${results.total}`);
    console.log(`Sincronizadas exitosamente: ${results.synced}`);
    console.log(`Errores: ${results.errors.length}`);
    
    if (results.errors.length > 0) {
      console.log('\nErrores encontrados:');
      results.errors.forEach(error => {
        console.log(`- ${error.conversationId}: ${error.error}`);
      });
    }
    
    // Mostrar estadísticas
    const totalSaved = await Conversation.count();
    const withAudio = await Conversation.count({ where: { audio_data: { [Op.ne]: null } } });
    const withTranscript = await Conversation.count({ where: { transcript: { [Op.ne]: null } } });
    
    console.log('\n=== ESTADÍSTICAS ===');
    console.log(`Total guardadas en DB: ${totalSaved}`);
    console.log(`Con audio: ${withAudio}`);
    console.log(`Con transcript: ${withTranscript}`);
    
    process.exit(0);
  } catch (error) {
    console.error('Error en sincronización:', error.message);
    process.exit(1);
  }
}

cleanAndSync();