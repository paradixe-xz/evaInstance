const sequelize = require('../config/database');
const Conversation = require('../models/Conversation');
const { Op } = require('sequelize');

async function showLeadsQuick() {
  try {
    await sequelize.authenticate();
    console.log('✅ Conectado a la base de datos');
    
    // Buscar conversaciones con datos de leads
    const conversations = await Conversation.findAll({
      where: {
        [Op.or]: [
          { evaluation_criteria_result: { [Op.ne]: null } },
          { data_collection_ok: 'true' },
          { data_collection_edad: { [Op.ne]: null } },
          { data_collection_number: { [Op.ne]: null } },
          { lead_number: { [Op.ne]: null } }
        ]
      },
      order: [['id', 'DESC']],
      limit: 20
    });

    console.log('\n🎯 === LEADS RECIENTES (últimos 20) ===');
    console.log('='.repeat(60));

    conversations.forEach((conv, index) => {
      console.log(`\n${index + 1}. 💼 ${conv.conversation_id}`);
      console.log(`📱 Teléfono: ${conv.lead_number || conv.data_collection_number || '❌'}`);
      console.log(`🎂 Edad: ${conv.data_collection_edad || '❌'}`);
      console.log(`✅ Evaluación: ${conv.evaluation_criteria_result || '❌'}`);
      console.log(`📊 Estado: ${conv.status || '❌'}`);
      console.log(`🤖 Agente: ${conv.agent_id || '❌'}`);
      
      if (conv.evaluation_criteria_rationale) {
        console.log(`💭 Razón: ${conv.evaluation_criteria_rationale.substring(0, 80)}...`);
      }
    });

    console.log('\n='.repeat(60));
    console.log(`📊 Total mostrado: ${conversations.length} conversaciones`);

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await sequelize.close();
  }
}

if (require.main === module) {
  showLeadsQuick();
}

module.exports = showLeadsQuick;